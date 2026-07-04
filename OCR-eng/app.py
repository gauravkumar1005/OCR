from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request

from services.callback_service import CallbackService
from services.document_pipeline import DocumentPipeline
from services.job_service_refactored import JobService
from services.storage_service import StorageService

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
TEMP_ROOT = BASE_DIR / "temp"

# Development timeout.
# Local OCR processing may take several minutes.
# Reduce this value before production deployment.
# TODO: Restore a production callback timeout of 30-60 seconds once asynchronous callback processing is finalized.
CALLBACK_TIMEOUT = (10, 1200)

document_pipeline = DocumentPipeline()
logger.info("OCR_ENGINE env raw value: %s", os.getenv("OCR_ENGINE", "<unset>"))
logger.info("OCR_ENGINE config value: %s", document_pipeline.ocr_service.engine)
logger.info("Selected OCR Engine: %s", document_pipeline.ocr_service.engine_display_name)
if document_pipeline.ocr_service.engine_display_name == "Qwen2.5-VL (Ollama)":
    logger.info("OCR flow: Qwen2.5-VL (Ollama) is active; PaddleOCR is bypassed for page processing")
else:
    logger.info("OCR flow: PaddleOCR is active for page processing")

job_service = JobService(
    storage_service=StorageService(TEMP_ROOT),
    document_pipeline=document_pipeline,
    callback_service=CallbackService(CALLBACK_TIMEOUT),
)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/ocr/process")
def process_ocr():
    request_data = request.get_json(silent=True) or {}
    result = job_service.process_job(request_data)

    status_code = result.pop("status_code", 202)
    if status_code != 202:
        return jsonify(result), status_code

    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
