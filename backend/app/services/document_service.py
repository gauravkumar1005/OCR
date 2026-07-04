from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from bson import ObjectId
from fastapi import UploadFile

from app.core.config import Settings
from app.exceptions.base import NotFoundException, ValidationException
from app.models.common import OCRStatus, ProcessingStatus, UploadStatus
from app.models.document import DocumentModel
from app.repositories.document_repository import DocumentRepository
from app.schemas.request import OCRCallbackRequest
from app.schemas.response import (
    APIResponse,
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentResponse,
    DocumentSummaryResponse,
    OCRCallbackResponse,
)
from app.services.cloudinary_service import CloudinaryService
from app.services.mapper_service import MapperService
from app.services.ocr_client import OCRClient

logger = logging.getLogger(__name__)


class DocumentService:
    """Business logic for document uploads and OCR callback updates."""

    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        cloudinary_service: CloudinaryService,
        ocr_client: OCRClient,
        mapper_service: MapperService,
        settings: Settings,
    ) -> None:
        self.document_repository = document_repository
        self.cloudinary_service = cloudinary_service
        self.ocr_client = ocr_client
        self.mapper_service = mapper_service
        self.settings = settings
        self._pending_ocr_tasks: set[asyncio.Task[Any]] = set()

    async def upload_document(
        self,
        claim_id: str,
        file: UploadFile,
        document_type: str | None = None,
    ) -> APIResponse[DocumentResponse]:
        normalized_claim_id = (claim_id or "").strip()
        if not normalized_claim_id:
            raise ValidationException("Claim id is required")

        normalized_document_type = (document_type or "combined_document").strip() or "combined_document"
        logger.info(
            "Upload started claim_id=%s document_type=%s filename=%s content_type=%s",
            normalized_claim_id,
            normalized_document_type,
            file.filename,
            file.content_type,
        )
        file_bytes = await file.read()
        logger.info("Upload completed claim_id=%s file_size_bytes=%s", normalized_claim_id, len(file_bytes))
        self._validate_upload(file, file_bytes)

        cloudinary_result: dict[str, str] | None = None
        created_document: DocumentModel | None = None

        try:
            cloudinary_result = await self.cloudinary_service.upload_file(
                file_bytes=file_bytes,
                file_name=file.filename or "document",
                mime_type=file.content_type or "application/octet-stream",
            )
            logger.info(
                "Cloudinary upload completed claim_id=%s secure_url=%s public_id=%s",
                normalized_claim_id,
                cloudinary_result.get("secure_url"),
                cloudinary_result.get("public_id"),
            )
            created_document = await self.document_repository.create(
                DocumentModel(
                    claim_id=normalized_claim_id,
                    document_type=normalized_document_type,
                    file_name=file.filename or "document",
                    mime_type=file.content_type or "application/octet-stream",
                    cloudinary_url=cloudinary_result["secure_url"],
                    cloudinary_public_id=cloudinary_result["public_id"],
                    cloudinary_resource_type=cloudinary_result.get("resource_type", "raw"),
                    upload_status=UploadStatus.UPLOADED,
                    processing_status=ProcessingStatus.OCR_IN_PROGRESS,
                    ocr_status=OCRStatus.PROCESSING,
                    file_size=len(file_bytes),
                )
            )
            logger.info(
                "Document saved document_id=%s claim_id=%s processing_status=%s ocr_status=%s",
                created_document.id,
                created_document.claim_id,
                created_document.processing_status,
                created_document.ocr_status,
            )

            logger.info("Preparing OCR payload document_id=%s", created_document.id)
            try:
                task = asyncio.create_task(
                    self._dispatch_ocr(
                        claim_id=normalized_claim_id,
                        document=created_document,
                        document_type=normalized_document_type,
                    )
                )
            except RuntimeError:
                logger.exception("Failed to schedule OCR dispatch task; running inline document_id=%s", created_document.id)
                await self._dispatch_ocr(
                    claim_id=normalized_claim_id,
                    document=created_document,
                    document_type=normalized_document_type,
                )
            else:
                self._track_background_task(task, document_id=str(created_document.id), label="OCR dispatch")
                logger.info("OCR dispatch scheduled document_id=%s task_id=%s", created_document.id, id(task))

            return APIResponse.ok(
                self._to_document_response(created_document),
                message="Document uploaded successfully",
            )
        except Exception:
            if created_document is not None:
                try:
                    await self.document_repository.update_statuses(
                        str(created_document.id),
                        upload_status=UploadStatus.FAILED,
                        processing_status=ProcessingStatus.FAILED,
                    )
                except Exception:
                    pass
            if cloudinary_result is not None:
                try:
                    await self.cloudinary_service.delete_file(
                        public_id=cloudinary_result["public_id"],
                        resource_type=cloudinary_result.get("resource_type", "raw"),
                    )
                except Exception:
                    pass
            raise

    async def list_documents(self, claim_id: str) -> list[DocumentSummaryResponse]:
        items = await self.document_repository.list_by_claim_id(claim_id)
        return [self._to_document_summary(item) for item in items]

    async def get_document(self, document_id: str) -> APIResponse[DocumentDetailResponse]:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise NotFoundException("Document not found")

        return APIResponse.ok(self._to_document_detail_response(document))

    async def get_raw_ocr(self, document_id: str) -> APIResponse[dict[str, Any] | None]:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise NotFoundException("Document not found")

        return APIResponse.ok(document.raw_ocr)

    async def get_mapped_data(self, document_id: str) -> APIResponse[dict[str, Any] | None]:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise NotFoundException("Document not found")

        return APIResponse.ok(document.mapped_data)

    async def delete_document(self, document_id: str) -> APIResponse[DeleteDocumentResponse]:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise NotFoundException("Document not found")

        await self.document_repository.soft_delete(document_id)
        try:
            await self.cloudinary_service.delete_file(
                public_id=document.cloudinary_public_id,
                resource_type=document.cloudinary_resource_type,
            )
        except Exception:
            pass
        return APIResponse.ok(DeleteDocumentResponse(document_id=document_id), message="Document deleted successfully")

    async def handle_ocr_callback(self, payload: OCRCallbackRequest) -> APIResponse[OCRCallbackResponse]:
        callback_started_at = time.perf_counter()
        logger.info("Callback received document_id=%s ocr_status=%s", payload.document_id, payload.ocr_status)

        if not ObjectId.is_valid(payload.document_id):
            raise ValidationException("Invalid document id")

        document = await self.document_repository.get_by_id(payload.document_id)
        if document is None:
            raise NotFoundException("Document not found")

        callback_status = payload.ocr_status
        callback_error = payload.error or ("OCR callback reported failure" if callback_status == OCRStatus.FAILED else None)
        update_fields: dict[str, Any] = {
            "ocr_status": callback_status,
            "raw_ocr": payload.raw_ocr_response,
            "error": callback_error,
        }

        task: asyncio.Task[Any] | None = None

        if callback_status == OCRStatus.COMPLETED:
            update_fields["processing_status"] = ProcessingStatus.OCR_COMPLETED
        elif callback_status == OCRStatus.FAILED:
            update_fields["processing_status"] = ProcessingStatus.FAILED
        else:
            update_fields["processing_status"] = document.processing_status

        matched_count, modified_count = await self.document_repository.update_document_fields(
            payload.document_id,
            update_fields,
        )
        logger.info(
            "Raw OCR saved document_id=%s matched_count=%s modified_count=%s",
            payload.document_id,
            matched_count,
            modified_count,
        )

        if callback_status == OCRStatus.COMPLETED:
            try:
                task = asyncio.create_task(self.process_mapping(payload.document_id))
            except RuntimeError:
                logger.exception("Failed to schedule background mapper document_id=%s", payload.document_id)
                await self.process_mapping(payload.document_id)
            else:
                self._track_background_task(task, document_id=payload.document_id, label="mapping")
                logger.info("Background mapper scheduled document_id=%s task_id=%s", payload.document_id, id(task))

        logger.info(
            "HTTP response returned for callback document_id=%s elapsed_seconds=%.3f",
            payload.document_id,
            time.perf_counter() - callback_started_at,
        )

        return APIResponse.ok(
            OCRCallbackResponse(
                document_id=payload.document_id,
                ocr_status=callback_status,
                matched_count=matched_count,
                modified_count=modified_count,
            ),
            message="OCR callback processed successfully",
        )

    async def process_mapping(self, document_id: str) -> None:
        started_at = time.perf_counter()
        logger.info("Background mapper started document_id=%s", document_id)

        try:
            document = await self.document_repository.get_by_id(document_id)
            if document is None:
                logger.warning("Background mapper skipped missing document_id=%s", document_id)
                return

            raw_ocr_payload = document.raw_ocr or {}
            if not raw_ocr_payload:
                logger.warning("Background mapper found no raw OCR document_id=%s", document_id)
                await self.document_repository.update_statuses(
                    document_id,
                    processing_status=ProcessingStatus.FAILED,
                    extra_fields={"error": "Raw OCR payload not available"},
                )
                return

            await self.document_repository.update_statuses(
                document_id,
                processing_status=ProcessingStatus.MAPPING_IN_PROGRESS,
            )

            mapped_data = await self.mapper_service.map_ocr_result(raw_ocr_payload, document_type=document.document_type)
            await self.document_repository.update_document_fields(
                document_id,
                {
                    "mapped_data": mapped_data,
                    "processing_status": ProcessingStatus.COMPLETED,
                    "error": None,
                },
            )
            logger.info(
                "Background mapper completed document_id=%s execution_time_seconds=%.3f",
                document_id,
                time.perf_counter() - started_at,
            )
        except Exception as exc:
            logger.exception("Background mapper failed document_id=%s", document_id)
            try:
                await self.document_repository.update_statuses(
                    document_id,
                    processing_status=ProcessingStatus.FAILED,
                    extra_fields={"error": str(exc)},
                )
            except Exception:
                logger.exception("Failed to persist mapper failure document_id=%s", document_id)
        finally:
            logger.info(
                "Mapper execution time document_id=%s seconds=%.3f",
                document_id,
                time.perf_counter() - started_at,
            )

    async def _dispatch_ocr(
        self,
        *,
        claim_id: str,
        document: DocumentModel,
        document_type: str,
    ) -> None:
        payload = {
            "document_id": str(document.id),
            "claim_id": claim_id,
            "document_type": document_type,
            "file_url": document.cloudinary_url,
            "mime_type": document.mime_type,
            "callback_url": "http://127.0.0.1:8000/api/ocr/callback",
        }
        logger.info("OCR dispatch started for document_id=%s", document.id)
        logger.info("OCR URL=%s", self.ocr_client.get_request_url())
        logger.info("OCR payload keys: %s", sorted(payload.keys()))
        logger.debug("OCR payload body for document_id=%s: %s", document.id, payload)

        try:
            logger.info("Calling OCR endpoint for document_id=%s", document.id)
            response = await asyncio.to_thread(self.ocr_client.process_document, payload)
            logger.info("OCR request sent for document_id=%s", document.id)
            logger.info(
                "OCR response received for document_id=%s: status_code=%s body=%s",
                document.id,
                response.get("status_code"),
                response.get("body"),
            )

            accepted = int(response.get("status_code", 0)) == 202
            response_json = response.get("json") or {}
            if not accepted:
                error_message = response_json.get("error") or response.get("body") or "OCR dispatch rejected"
                await self.document_repository.update_statuses(
                    str(document.id),
                    processing_status=ProcessingStatus.FAILED,
                    extra_fields={
                        "ocr_status": OCRStatus.FAILED,
                        "error": error_message,
                    },
                )
                return

            logger.info("OCR engine accepted request for document_id=%s", document.id)
            logger.info("OCR dispatch completed for document_id=%s", document.id)
        except Exception as exc:
            logger.exception("OCR dispatch failed for document_id=%s", document.id)
            await self.document_repository.update_statuses(
                str(document.id),
                processing_status=ProcessingStatus.FAILED,
                extra_fields={
                    "ocr_status": OCRStatus.FAILED,
                    "error": str(exc),
                },
            )

    def _validate_upload(self, file: UploadFile, file_bytes: bytes) -> None:
        if file.content_type not in self.settings.ALLOWED_MIME_TYPES:
            raise ValidationException("Only PDF, PNG, JPG and JPEG files are allowed")
        if len(file_bytes) > self.settings.MAX_UPLOAD_SIZE:
            raise ValidationException("File exceeds the configured maximum upload size")
        if not file.filename:
            raise ValidationException("File name is required")

    def _to_document_response(self, document: DocumentModel) -> DocumentResponse:
        return DocumentResponse(
            document_id=str(document.id),
            claim_id=document.claim_id,
            document_type=document.document_type,
            file_name=document.file_name,
            mime_type=document.mime_type,
            cloudinary_url=document.cloudinary_url,
            upload_status=document.upload_status,
            processing_status=document.processing_status,
            ocr_status=document.ocr_status,
            error=document.error,
            file_size=document.file_size,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _to_document_detail_response(self, document: DocumentModel) -> DocumentDetailResponse:
        mapped_summary = None
        if isinstance(document.mapped_data, dict):
            summary = document.mapped_data.get("summary")
            if isinstance(summary, dict):
                mapped_summary = summary

        return DocumentDetailResponse(
            document_id=str(document.id),
            claim_id=document.claim_id,
            document_type=document.document_type,
            file_name=document.file_name,
            mime_type=document.mime_type,
            cloudinary_url=document.cloudinary_url,
            upload_status=document.upload_status,
            processing_status=document.processing_status,
            ocr_status=document.ocr_status,
            error=document.error,
            file_size=document.file_size,
            created_at=document.created_at,
            updated_at=document.updated_at,
            mapped_summary=mapped_summary,
        )

    def _to_document_summary(self, document: DocumentModel) -> DocumentSummaryResponse:
        return DocumentSummaryResponse(
            document_id=str(document.id),
            document_type=document.document_type,
            processing_status=document.processing_status,
        )

    def _track_background_task(self, task: asyncio.Task[Any], *, document_id: str, label: str) -> None:
        self._pending_ocr_tasks.add(task)
        logger.debug("Tracking %s task document_id=%s task_id=%s", label, document_id, id(task))

        def _on_done(completed_task: asyncio.Task[Any]) -> None:
            self._pending_ocr_tasks.discard(completed_task)
            try:
                exception = completed_task.exception()
            except asyncio.CancelledError:
                logger.exception("%s task was cancelled document_id=%s task_id=%s", label, document_id, id(completed_task))
                return
            except Exception:
                logger.exception("Failed to inspect %s task completion document_id=%s task_id=%s", label, document_id, id(completed_task))
                return

            if exception is not None:
                logger.exception(
                    "%s task failed document_id=%s task_id=%s error=%s",
                    label,
                    document_id,
                    id(completed_task),
                    exception,
                )
            else:
                logger.info("%s task finished document_id=%s task_id=%s", label, document_id, id(completed_task))

        task.add_done_callback(_on_done)
