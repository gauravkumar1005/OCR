from __future__ import annotations

import json
import logging
import shutil
import threading
import traceback
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

try:
    from bson import ObjectId
except Exception:  # pragma: no cover - local fallback when bson is unavailable
    ObjectId = None

from OCR_Extraction_folder.multimodal_extractor import multimodal_extract
from OCR_Extraction_folder.pdf_converter import convert_pdf_to_images

app = Flask(__name__)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
TEMP_ROOT = BASE_DIR / "temp"
INPUT_ROOT = TEMP_ROOT / "input"
OUTPUT_ROOT = TEMP_ROOT / "output"


def _is_valid_document_id(document_id: str) -> bool:
    if not document_id:
        return False
    if ObjectId is None:
        return True
    return ObjectId.is_valid(document_id)


def _safe_filename_from_url(file_url: str, document_id: str) -> str:
    parsed = urlparse(file_url)
    suffix = Path(parsed.path).suffix or ".pdf"
    return f"{document_id}{suffix}"


def _download_file(file_url: str, document_id: str) -> Path:
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename_from_url(file_url, document_id)
    destination = INPUT_ROOT / filename

    logger.info("Downloading file_url=%s to %s", file_url, destination)
    response = requests.get(file_url, stream=True, timeout=(10, 60))
    response.raise_for_status()

    with destination.open("wb") as file_handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file_handle.write(chunk)

    return destination


def _run_existing_pipeline(downloaded_path: Path, document_id: str) -> dict:
    document_root = OUTPUT_ROOT / document_id
    image_root = document_root / "images"
    json_root = document_root / "json"
    image_root.mkdir(parents=True, exist_ok=True)
    json_root.mkdir(parents=True, exist_ok=True)

    if downloaded_path.suffix.lower() == ".pdf":
        logger.info("Converting PDF to images at %s", image_root)
        image_paths = convert_pdf_to_images(str(downloaded_path), str(image_root))
    else:
        image_paths = [str(downloaded_path)]

    logger.info("Pipeline started for %s with %d page(s)", document_id, len(image_paths))
    page_outputs: list[dict] = []

    for page_number, image_path in enumerate(image_paths, start=1):
        page_folder = json_root / f"page_{page_number:03d}"
        page_folder.mkdir(parents=True, exist_ok=True)
        page_result = multimodal_extract(image_path, output_folder=str(page_folder))

        generated_json_path = page_folder / f"{Path(image_path).stem}_ocr.json"
        generated_json = page_result
        if generated_json_path.exists():
            generated_json = json.loads(generated_json_path.read_text(encoding="utf-8"))

        page_outputs.append(
            {
                "page_number": page_number,
                "image_path": image_path,
                "ocr_json_path": str(generated_json_path),
                "generated_json": generated_json,
            }
        )

    combined_text = "\n\n".join(
        str(page.get("generated_json", {}).get("full_text") or page.get("generated_json", {}).get("text") or "")
        for page in page_outputs
    ).strip()

    combined_output = {
        "document_id": document_id,
        "page_count": len(page_outputs),
        "pages": page_outputs,
        "combined_text": combined_text,
    }

    combined_json_path = document_root / f"{document_id}_ocr_output.json"
    combined_json_path.write_text(json.dumps(combined_output, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Pipeline completed for %s, output saved to %s", document_id, combined_json_path)
    return combined_output


def _send_callback(callback_url: str, payload: dict) -> requests.Response:
    logger.info("Callback started for %s", callback_url)
    response = requests.post(callback_url, json=payload, timeout=(10, 60))
    logger.info("Callback status code/body: %s | %s", response.status_code, response.text)
    response.raise_for_status()
    return response


def _process_ocr_job(data: dict) -> None:
    document_id = (data.get("document_id") or "").strip()
    file_url = (data.get("file_url") or "").strip()
    callback_url = (data.get("callback_url") or "").strip()
    document_type = (data.get("document_type") or "combined_document").strip() or "combined_document"

    try:
        logger.info("OCR background job started")
        logger.info("document_id=%s", document_id)
        logger.info("file_url=%s", file_url)

        downloaded_path = _download_file(file_url, document_id)
        logger.info("File downloaded path=%s", downloaded_path)
        logger.info("Pipeline started")
        combined_output = _run_existing_pipeline(downloaded_path, document_id)

        callback_payload = {
            "document_id": document_id,
            "ocr_status": "completed",
            "raw_ocr_response": combined_output,
            "structured_ocr_data": {
                "document_id": document_id,
                "document_type": document_type,
                "page_count": combined_output.get("page_count", 0),
                "combined_text": combined_output.get("combined_text", ""),
                "pages": combined_output.get("pages", []),
            },
            "mapped_fields": {
                "document_id": document_id,
                "document_type": document_type,
                "pages": [
                    {
                        "page_number": page.get("page_number"),
                        "metadata": page.get("generated_json", {}).get("metadata", {}),
                    }
                    for page in combined_output.get("pages", [])
                ],
            },
            "error": None,
        }

        _send_callback(callback_url, callback_payload)
        logger.info("OCR background job completed document_id=%s", document_id)
    except Exception as exc:
        logger.error("OCR processing failed for document_id=%s: %s", document_id, exc)
        logger.error(traceback.format_exc())
        if callback_url:
            try:
                failure_payload = {
                    "document_id": document_id,
                    "ocr_status": "failed",
                    "raw_ocr_response": None,
                    "structured_ocr_data": None,
                    "mapped_fields": None,
                    "error": f"{exc}",
                }
                _send_callback(callback_url, failure_payload)
            except Exception:
                logger.error("Failed to send OCR failure callback for document_id=%s", document_id)
                logger.error(traceback.format_exc())


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/ocr/process")
def process_ocr():
    data = request.get_json(silent=True) or {}

    document_id = (data.get("document_id") or "").strip()
    file_url = (data.get("file_url") or "").strip()
    callback_url = (data.get("callback_url") or "").strip()

    logger.info("OCR request received")
    logger.info("document_id=%s", document_id)
    logger.info("file_url=%s", file_url)

    if not _is_valid_document_id(document_id):
        return jsonify({"error": "invalid document_id"}), 400
    if not file_url:
        return jsonify({"error": "file_url required"}), 400
    if not callback_url:
        return jsonify({"error": "callback_url required"}), 400

    worker = threading.Thread(target=_process_ocr_job, args=(data,), daemon=True)
    worker.start()
    logger.info("OCR job queued document_id=%s thread_id=%s", document_id, worker.ident)

    return jsonify({
        "success": True,
        "document_id": document_id,
        "status": "processing",
    }), 202


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    app.run(host="0.0.0.0", port=8001, debug=True)
