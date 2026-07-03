from __future__ import annotations

from pymongo.errors import PyMongoError

from app.exceptions.base import DatabaseException
from app.models.mapped_result import MappedResultModel


class MappedRepository:
    """MongoDB operations for mapped results only."""

    async def create(self, mapped_result: MappedResultModel) -> MappedResultModel:
        try:
            await mapped_result.insert()
            return mapped_result
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to create mapped result") from exc

    async def get_latest_by_document_id(self, claim_id: str, document_id: str) -> MappedResultModel | None:
        try:
            return (
                await MappedResultModel.find(
                    MappedResultModel.claim_id == claim_id,
                    MappedResultModel.document_id == document_id,
                )
                .sort("-created_at")
                .first_or_none()
            )
        except Exception as exc:  # noqa: BLE001
            raise DatabaseException("Failed to fetch mapped result") from exc
