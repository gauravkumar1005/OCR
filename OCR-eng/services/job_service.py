from __future__ import annotations

import logging
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

try:
    from bson import ObjectId
except Exception:  # pragma: no cover - local fallback when bson is unavailable
    ObjectId = None

from .callback_service import CallbackService
from .ocr_service import OCRService
from .pdf_service import PDFService
from .storage_service import StorageService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OCRJobRequest:
    document_id: str
    file_url: str
    callback_url: str
    document_type: str = "combined_document"


class JobService:
    def __init__(
        self,
        *,
        storage_service: StorageService,
        pdf_service: PDFService,
        ocr_service: OCRService,
        callback_service: CallbackService,
    ) -> None:
        self.storage_service = storage_service
        self.pdf_service = pdf_service
        self.ocr_service = ocr_service
        self.callback_service = callback_service

    def process_job(self, request_data: dict[str, Any]) -> dict[str, Any]:
        document_id = (request_data.get("document_id") or "").strip()
        file_url = (request_data.get("file_url") or "").strip()
        callback_url = (request_data.get("callback_url") or "").strip()
        document_type = (request_data.get("document_type") or "combined_document").strip() or "combined_document"

        logger.info("OCR request received")
        logger.info("document_id=%s", document_id)
        logger.info("file_url=%s", file_url)

        if not self._is_valid_document_id(document_id):
            return {"error": "invalid document_id", "status_code": 400}
        if not file_url:
            return {"error": "file_url required", "status_code": 400}
        if not callback_url:
            return {"error": "callback_url required", "status_code": 400}

        job = OCRJobRequest(
            document_id=document_id,
            file_url=file_url,
            callback_url=callback_url,
            document_type=document_type,
        )

        worker = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        worker.start()
        logger.info("OCR job queued document_id=%s thread_id=%s", document_id, worker.ident)
        return {"success": True, "document_id": document_id, "status": "processing", "status_code": 202}

    def _run_job(self, job: OCRJobRequest) -> None:
        try:
            logger.info("OCR job started document_id=%s", job.document_id)
            downloaded_path = self._download_pdf(job.file_url, job.document_id)
            logger.info("PDF downloaded document_id=%s path=%s", job.document_id, downloaded_path)

            directories = self.storage_service.prepare_job_directories(job.document_id)
            image_paths = self.pdf_service.convert_pdf_to_images(downloaded_path, directories["image_root"])
            logger.info("Image conversion completed document_id=%s page_count=%d", job.document_id, len(image_paths))

            combined_output = self._run_ocr_pages(job.document_id, image_paths, directories["json_root"])
            logger.info("Merged OCR completed document_id=%s", job.document_id)

            callback_payload = self._build_callback_payload(job, combined_output)
            logger.info("Callback payload generated document_id=%s", job.document_id)
            self.callback_service.send_callback(job.callback_url, callback_payload)
            logger.info("Callback successful document_id=%s", job.document_id)
            logger.info("OCR job completed document_id=%s", job.document_id)
        except Exception as exc:
            logger.error("OCR job failed document_id=%s error=%s", job.document_id, exc)
            logger.error(traceback.format_exc())
            if job.callback_url:
                try:
                    failure_payload = {
                        "document_id": job.document_id,
                        "ocr_status": "failed",
                        "raw_ocr_response": None,
                        "structured_ocr_data": None,
                        "mapped_fields": None,
                        "error": f"{exc}",
                    }
                    self.callback_service.send_callback(job.callback_url, failure_payload)
                except Exception:
                    logger.error("Failed to send OCR failure callback document_id=%s", job.document_id)
                    logger.error(traceback.format_exc())

    def _download_pdf(self, file_url: str, document_id: str) -> Path:
        self.storage_service.input_root.mkdir(parents=True, exist_ok=True)
        destination = self.storage_service.input_root / self._safe_filename_from_url(file_url, document_id)
        logger.info("Downloading file_url=%s to %s", file_url, destination)
        response = requests.get(file_url, stream=True, timeout=(10, 60))
        response.raise_for_status()
        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file_handle.write(chunk)
        return destination

    def _run_ocr_pages(self, document_id: str, image_paths: list[str], json_root: Path) -> dict[str, Any]:
        logger.info("OCR page processing started document_id=%s", document_id)
        page_outputs: list[dict[str, Any]] = []

        for page_number, image_path in enumerate(image_paths, start=1):
            page_folder = json_root / f"page_{page_number:03d}"
            page_folder.mkdir(parents=True, exist_ok=True)
            logger.info("OCR page %d started document_id=%s", page_number, document_id)
            generated_json = self.ocr_service.run_page_ocr(image_path, page_folder)
            page_outputs.append(
                {
                    "page_number": page_number,
                    "image_path": image_path,
                    "ocr_json_path": str(page_folder / f"{Path(image_path).stem}_ocr.json"),
                    "generated_json": generated_json,
                }
            )
            logger.info("OCR page %d completed document_id=%s", page_number, document_id)

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

        document_root = self.storage_service.output_root / document_id
        self.storage_service.write_json(document_root / f"{document_id}_ocr_output.json", combined_output)
        return combined_output

    def _build_callback_payload(self, job: OCRJobRequest, combined_output: dict[str, Any]) -> dict[str, Any]:
        return {
            "document_id": job.document_id,
            "ocr_status": "completed",
            "raw_ocr_response": combined_output,
            "structured_ocr_data": {
                "document_id": job.document_id,
                "document_type": job.document_type,
                "page_count": combined_output.get("page_count", 0),
                "combined_text": combined_output.get("combined_text", ""),
                "pages": combined_output.get("pages", []),
            },
            "mapped_fields": {
                "document_id": job.document_id,
                "document_type": job.document_type,
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

    def _is_valid_document_id(self, document_id: str) -> bool:
        if not document_id:
            return False
        if ObjectId is None:
            return True
        return ObjectId.is_valid(document_id)

    @staticmethod
    def _safe_filename_from_url(file_url: str, document_id: str) -> str:
        parsed = urlparse(file_url)
        suffix = Path(parsed.path).suffix or ".pdf"
        return f"{document_id}{suffix}"
