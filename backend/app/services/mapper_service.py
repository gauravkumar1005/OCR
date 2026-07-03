from __future__ import annotations

from typing import Any

import asyncio
import logging

from app.core.config import Settings
from app.exceptions.base import MapperConfigurationException
from app.services.mapper.mapper_factory import MapperFactory

logger = logging.getLogger(__name__)


class MapperService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.factory = MapperFactory()

    async def map_ocr_result(self, raw_json: dict[str, Any], document_type: str | None = None) -> dict[str, Any]:
        mapper = self.factory.get_mapper(document_type)
        try:
            return await asyncio.to_thread(mapper.map, raw_json, document_type)
        except MapperConfigurationException as exc:
            logger.exception("Mapper configuration missing for document_type=%s", document_type)
            return mapper._empty_result(raw_json or {}, document_type or mapper.document_type)
