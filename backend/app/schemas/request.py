from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import OCRStatus


class DocumentSearchQuery(BaseModel):
    """Query parameters for claim-scoped document search."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    claim_id: str = Field(alias="claimId", min_length=1, max_length=64)


class OCRCallbackRequest(BaseModel):
    """Payload received from the OCR engine after processing."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    document_id: str = Field(min_length=1)
    ocr_status: OCRStatus
    raw_ocr_response: dict[str, Any] | None = None
    structured_ocr_data: dict[str, Any] | None = None
    mapped_fields: dict[str, Any] | None = None
    error: str | None = None
