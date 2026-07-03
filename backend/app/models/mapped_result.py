from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from beanie import Document
from pydantic import Field


class MappedResultModel(Document):
    """Mapper output persisted for future frontend consumption."""

    claim_id: str
    document_id: str
    mapper_version: str
    mapped_json: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "mapped_results"
