from __future__ import annotations

from pymongo.errors import PyMongoError

from app.exceptions.base import DatabaseException
from app.models.ocr_result import OCRResultModel


class OCRRepository:
    """MongoDB operations for OCR results only."""

    async def create(self, ocr_result: OCRResultModel) -> OCRResultModel:
        try:
            await ocr_result.insert()
            return ocr_result
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to create OCR result") from exc

    async def get_latest_by_document_id(self, claim_id: str, document_id: str) -> OCRResultModel | None:
        try:
            return (
                await OCRResultModel.find(
                    OCRResultModel.claim_id == claim_id,
                    OCRResultModel.document_id == document_id,
                )
                .sort("-processed_at")
                .first_or_none()
            )
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to fetch OCR result") from exc
