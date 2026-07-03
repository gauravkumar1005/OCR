from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import Settings
from app.models.document import DocumentModel
from app.models.mapped_result import MappedResultModel
from app.models.ocr_result import OCRResultModel


async def init_db(settings: Settings) -> AsyncIOMotorClient:
    """Initialize MongoDB and register all Beanie documents."""

    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client[settings.DATABASE_NAME]
    await init_beanie(
        database=database,
        document_models=[DocumentModel, OCRResultModel, MappedResultModel],
    )
    return client
