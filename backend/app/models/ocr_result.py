from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from beanie import Document
from pydantic import Field


class OCRResultModel(Document):
    """Raw OCR payload persisted exactly as returned by the external service."""

    claim_id: str
    document_id: str
    provider: str
    raw_json: dict[str, Any]
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ocr_results"
