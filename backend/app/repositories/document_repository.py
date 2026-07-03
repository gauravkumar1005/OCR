from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from bson import ObjectId

from app.exceptions.base import DatabaseException, ValidationException
from app.models.common import OCRStatus, ProcessingStatus, UploadStatus
from app.models.document import DocumentModel


class DocumentRepository:
    """MongoDB operations for documents only."""

    async def create(self, document: DocumentModel) -> DocumentModel:
        try:
            await document.insert()
            return document
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to create document") from exc

    async def get_by_id(self, document_id: str) -> DocumentModel | None:
        if not ObjectId.is_valid(document_id):
            raise ValidationException("Invalid document id")
        try:
            return await DocumentModel.find_one(
                DocumentModel.id == ObjectId(document_id),
                DocumentModel.is_deleted == False,  # noqa: E712
            )
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to fetch document") from exc

    async def list_by_claim_id(self, claim_id: str) -> list[DocumentModel]:
        if not claim_id:
            raise ValidationException("Claim id is required")
        try:
            return await DocumentModel.find(
                DocumentModel.claim_id == claim_id,
                DocumentModel.is_deleted == False,  # noqa: E712
            ).sort("-created_at").to_list()
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to list documents") from exc

    async def update_statuses(
        self,
        document_id: str,
        *,
        upload_status: UploadStatus | None = None,
        processing_status: ProcessingStatus | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> DocumentModel | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        if upload_status is not None:
            document.upload_status = upload_status
        if processing_status is not None:
            document.processing_status = processing_status
        if extra_fields:
            for key, value in extra_fields.items():
                setattr(document, key, value)
        document.updated_at = datetime.now(timezone.utc)

        try:
            await document.save()
            return document
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to update document") from exc

    async def update_document_fields(self, document_id: str, extra_fields: dict[str, Any]) -> tuple[int, int]:
        if not ObjectId.is_valid(document_id):
            raise ValidationException("Invalid document id")

        payload = self._normalize_mongo_value(dict(extra_fields))
        payload["updated_at"] = datetime.now(timezone.utc)

        try:
            result = await DocumentModel.get_motor_collection().update_one(
                {"_id": ObjectId(document_id), "is_deleted": False},
                {"$set": payload},
            )
            return result.matched_count, result.modified_count
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to update document") from exc

    async def soft_delete(self, document_id: str) -> DocumentModel | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.is_deleted = True
        document.deleted_at = datetime.now(timezone.utc)
        document.updated_at = datetime.now(timezone.utc)

        try:
            await document.save()
            return document
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to delete document") from exc

    def _normalize_mongo_value(self, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: self._normalize_mongo_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._normalize_mongo_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._normalize_mongo_value(item) for item in value]
        return value
