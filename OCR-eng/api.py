from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

ENGINE_ROOT = Path(__file__).resolve().parent

# One JSON file per run_id, written by main.py at each pipeline checkpoint
# and read here by GET /status/{run_id}. File-based because main.py runs as
# a separate subprocess - this is the simplest way for it to hand progress
# back to this (long-lived) API process without extra network calls.
PROGRESS_DIR = ENGINE_ROOT / "runs"
PROGRESS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Claim OCR Engine", version="1.0.0")


class OCRJobRequest(BaseModel):
    claim_id: str
    document_id: str
    document_type: str
    file_url: str
    mime_type: str
    callback_url: str
    pdf_path: Optional[str] = None
    source_file_url: Optional[str] = None
    max_pages: Optional[int] = None
    test_mode: Optional[bool] = None


class OCRJobResponse(BaseModel):
    status: str
    pid: int
    run_id: str
    claim_id: str
    document_id: str
    document_type: str
    file_url: str
    mime_type: str
    callback_url: str
    engine_script: str


def _send_failure_callback(
    callback_url: str,
    claim_id: str,
    document_id: str,
    document_type: str,
    error_message: str,
) -> None:
    """Best-effort notification to the backend when the OCR subprocess dies
    before it could send its own callback (crash, OOM-kill, unhandled
    exception). Without this, the claim would sit in "processing" forever
    since main.py never got a chance to report failure itself."""
    if not callback_url:
        print(f"[SUPERVISOR] No callback_url for claim={claim_id}, cannot report crash")
        return

    body = json.dumps(
        {
            "claim_id": claim_id,
            "document_id": document_id,
            "document_type": document_type,
            "ocr_status": "failed",
            "error_message": error_message,
        }
    ).encode("utf-8")

    last_error = None
    for attempt in range(1, 4):
        is_client_error = False
        for method in ("PATCH", "POST"):
            try:
                request = urllib_request.Request(
                    callback_url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method=method,
                )
                with urllib_request.urlopen(request, timeout=30) as response:
                    print(
                        f"[SUPERVISOR] Crash callback delivered via {method} "
                        f"for claim={claim_id} - HTTP {response.status}"
                    )
                return
            except urllib_error.HTTPError as exc:
                body_text = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
                last_error = f"HTTP {exc.code}: {body_text or exc.reason}"
                if exc.code < 500:
                    is_client_error = True
            except Exception as exc:
                last_error = str(exc)

        if is_client_error:
            print(
                f"[SUPERVISOR] Not retrying crash callback for claim={claim_id} "
                "- backend rejected the request (4xx)."
            )
            break
        if attempt < 3:
            time.sleep(2 * attempt)

    print(
        f"[SUPERVISOR] Could not deliver crash callback for claim={claim_id}: {last_error}"
    )


async def _supervise_job(proc: subprocess.Popen, payload: OCRJobRequest, run_id: str) -> None:
    """Watches the OCR subprocess in the background. If main.py crashes
    (non-zero exit code) before sending its own callback, this is the
    safety net that tells the backend the job failed - so the claim
    doesn't get stuck in "processing" indefinitely."""
    returncode = await asyncio.to_thread(proc.wait)
    if returncode == 0:
        return

    print(
        f"[SUPERVISOR] OCR engine process for claim={payload.claim_id} "
        f"document={payload.document_id} exited with code {returncode}"
    )
    error_message = (
        f"OCR engine process exited unexpectedly with code {returncode}. "
        f"Check engine logs (pid was {proc.pid}) for details."
    )
    _write_progress(
        run_id,
        {
            "claim_id": payload.claim_id,
            "document_id": payload.document_id,
            "document_type": payload.document_type,
            "stage": "failed",
            "stage_label": "Failed",
            "percent": 100,
            "status": "failed",
            "message": error_message,
        },
    )
    await asyncio.to_thread(
        _send_failure_callback,
        payload.callback_url,
        payload.claim_id,
        payload.document_id,
        payload.document_type,
        error_message,
    )


def _write_progress(run_id: str, data: dict) -> None:
    payload = {**data, "run_id": run_id, "updated_at": _utc_now_iso()}
    try:
        (PROGRESS_DIR / f"{run_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as exc:
        print(f"[PROGRESS] Failed to write progress file for run_id={run_id}: {exc}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _launch_job(payload: OCRJobRequest) -> tuple[int, str]:
    run_id = uuid.uuid4().hex

    env = os.environ.copy()
    env["OCR_CALLBACK_URL"] = payload.callback_url
    env["OCR_RUN_ID"] = run_id
    env["OCR_CLAIM_ID"] = payload.claim_id
    env["OCR_DOCUMENT_ID"] = payload.document_id
    env["OCR_DOCUMENT_TYPE"] = payload.document_type
    env["OCR_FILE_URL"] = payload.file_url
    env["OCR_MIME_TYPE"] = payload.mime_type
    if payload.max_pages is not None and payload.max_pages > 0:
        env["OCR_MAX_PAGES"] = str(payload.max_pages)
        env["MAX_PDF_PAGES"] = str(payload.max_pages)

    if payload.pdf_path:
        env["OCR_PDF_PATH"] = payload.pdf_path
    if payload.source_file_url:
        env["OCR_SOURCE_FILE_URL"] = payload.source_file_url
    if payload.test_mode is not None:
        env["OCR_TEST_MODE"] = "true" if payload.test_mode else "false"

    main_script = ENGINE_ROOT / "main.py"
    if not main_script.exists():
        raise FileNotFoundError(f"Engine entrypoint not found: {main_script}")

    _write_progress(
        run_id,
        {
            "claim_id": payload.claim_id,
            "document_id": payload.document_id,
            "document_type": payload.document_type,
            "stage": "queued",
            "stage_label": "Queued",
            "percent": 0,
            "status": "in_progress",
            "message": None,
        },
    )

    proc = subprocess.Popen(
        [sys.executable, str(main_script)],
        cwd=str(ENGINE_ROOT),
        env=env,
    )
    # Fire-and-forget: watches this specific process, sends a failure
    # callback to the backend if it crashes instead of finishing normally.
    asyncio.create_task(_supervise_job(proc, payload, run_id))
    return proc.pid, run_id


async def _run_job(payload: OCRJobRequest) -> OCRJobResponse:
    try:
        pid, run_id = _launch_job(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch OCR engine: {exc}")

    return OCRJobResponse(
        status="accepted",
        pid=pid,
        run_id=run_id,
        claim_id=payload.claim_id,
        document_id=payload.document_id,
        document_type=payload.document_type,
        file_url=payload.file_url,
        mime_type=payload.mime_type,
        callback_url=payload.callback_url,
        engine_script=str(ENGINE_ROOT / "main.py"),
    )


@app.post("/run", response_model=OCRJobResponse, status_code=202)
async def run_job(payload: OCRJobRequest, background_tasks: BackgroundTasks):
    return await _run_job(payload)


@app.post("/ocr/process", response_model=OCRJobResponse, status_code=202)
async def process_job(payload: OCRJobRequest, background_tasks: BackgroundTasks):
    return await _run_job(payload)


@app.get("/status/{run_id}")
async def get_status(run_id: str) -> Dict[str, Any]:
    """Current pipeline stage for a run, as last written by main.py (or the
    'queued' stage written right when the job was launched, if main.py
    hasn't started reporting yet). Read by the backend, which the frontend
    polls - the engine itself is never called directly by the browser."""
    path = PROGRESS_DIR / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Unknown run_id")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read progress file: {exc}")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "engine": "claim-ocr"}
