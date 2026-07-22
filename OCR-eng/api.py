from __future__ import annotations

import asyncio
import json
import os
import shutil
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
    # If set, reuse this run_id (and therefore the same RESULT/<job>/<run_id>/
    # checkpoint folder from a prior attempt) instead of generating a fresh
    # one, and tell main.py to skip stages it already completed. Set by the
    # backend's retry endpoint when re-dispatching a claim that previously
    # failed/was interrupted partway through.
    resume_run_id: Optional[str] = None


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
    # A resume request reuses the SAME run_id as the attempt it's resuming,
    # so main.py resolves to the same RESULT/<job>/<run_id>/ folder and
    # finds its previous checkpoints (converted images, per-page OCR/layout/
    # classification json, already-parsed LLM json) still sitting there.
    # A fresh request (no resume_run_id) always gets a brand new run_id.
    is_resume = bool(payload.resume_run_id)
    run_id = payload.resume_run_id if is_resume else uuid.uuid4().hex

    env = os.environ.copy()
    env["OCR_CALLBACK_URL"] = payload.callback_url
    env["OCR_RUN_ID"] = run_id
    env["OCR_RESUME"] = "true" if is_resume else "false"
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
            "stage": "resuming" if is_resume else "queued",
            "stage_label": "Resuming from checkpoint" if is_resume else "Queued",
            "percent": 0,
            "status": "in_progress",
            "message": None,
        },
    )

    print(
        f"[LAUNCH] {'Resuming' if is_resume else 'Starting'} OCR job "
        f"claim={payload.claim_id} document={payload.document_id} run_id={run_id}"
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


# ---------------------------------------------------------------------------
# BACKGROUND CLEANUP
# ---------------------------------------------------------------------------
# Every job writes a full RESULT/<run>/ folder (images, OCR json, layout
# crops, merged output...) plus a runs/<run_id>.json progress file, and
# temp/ can accumulate downloaded source PDFs. None of this was ever
# deleted, so disk usage only ever grows. This sweep periodically removes
# anything older than the retention window - safe to disable by setting
# OCR_CLEANUP_RETENTION_DAYS=0.
CLEANUP_INTERVAL_SECONDS = int(os.getenv("OCR_CLEANUP_INTERVAL_SECONDS", str(6 * 3600)))
CLEANUP_RETENTION_DAYS = float(os.getenv("OCR_CLEANUP_RETENTION_DAYS", "7"))


def _delete_if_older_than(path: Path, cutoff_ts: float) -> bool:
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return False
    if mtime >= cutoff_ts:
        return False
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        return True
    except Exception as exc:
        print(f"[CLEANUP] Could not remove {path}: {exc}")
        return False


def run_cleanup_once(retention_days: float | None = None) -> int:
    """Deletes RESULT/<run>/ folders, runs/<run_id>.json progress files,
    and temp/ contents older than the retention window. Returns the
    number of items removed. Exposed as a plain function (not just the
    background loop) so it's easy to call directly, e.g. from tests or a
    one-off `python -c "from api import run_cleanup_once; run_cleanup_once()"`."""
    days = CLEANUP_RETENTION_DAYS if retention_days is None else retention_days
    if days <= 0:
        return 0

    cutoff_ts = time.time() - days * 86400
    deleted = 0

    result_dir = ENGINE_ROOT / "RESULT"
    if result_dir.exists():
        for child in result_dir.iterdir():
            if _delete_if_older_than(child, cutoff_ts):
                deleted += 1

    if PROGRESS_DIR.exists():
        for child in PROGRESS_DIR.glob("*.json"):
            if _delete_if_older_than(child, cutoff_ts):
                deleted += 1

    temp_dir = ENGINE_ROOT / "temp"
    if temp_dir.exists():
        for child in temp_dir.iterdir():
            if _delete_if_older_than(child, cutoff_ts):
                deleted += 1

    if deleted:
        print(f"[CLEANUP] Removed {deleted} item(s) older than {days} day(s)")
    return deleted


async def _cleanup_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(run_cleanup_once)
        except Exception as exc:
            print(f"[CLEANUP] Sweep failed: {exc}")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


@app.on_event("startup")
async def _start_background_cleanup() -> None:
    if CLEANUP_RETENTION_DAYS > 0:
        asyncio.create_task(_cleanup_loop())
        print(
            f"[CLEANUP] Background sweep enabled - retention="
            f"{CLEANUP_RETENTION_DAYS}d, interval={CLEANUP_INTERVAL_SECONDS}s"
        )
    else:
        print("[CLEANUP] Disabled (OCR_CLEANUP_RETENTION_DAYS<=0)")
