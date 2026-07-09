from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

ENGINE_ROOT = Path(__file__).resolve().parent

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
    claim_id: str
    document_id: str
    document_type: str
    file_url: str
    mime_type: str
    callback_url: str
    engine_script: str


def _launch_job(payload: OCRJobRequest) -> int:
    env = os.environ.copy()
    env["OCR_CALLBACK_URL"] = payload.callback_url
    env["OCR_RUN_ID"] = uuid.uuid4().hex
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

    proc = subprocess.Popen(
        [sys.executable, str(main_script)],
        cwd=str(ENGINE_ROOT),
        env=env,
    )
    return proc.pid


async def _run_job(payload: OCRJobRequest) -> OCRJobResponse:
    try:
        pid = _launch_job(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to launch OCR engine: {exc}")

    return OCRJobResponse(
        status="accepted",
        pid=pid,
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


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "engine": "claim-ocr"}
