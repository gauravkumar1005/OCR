from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from beanie import Document, Indexed
from pydantic import Field

from app.models.common import OCRStatus, ProcessingStatus, UploadStatus


class DocumentModel(Document):
    """Uploaded document metadata linked to a claim id."""

    claim_id: Annotated[str, Indexed()] = Field(..., min_length=1, max_length=64)
    document_type: Optional[str] = None
    file_name: str
    mime_type: str
    cloudinary_url: str
    cloudinary_public_id: str
    cloudinary_resource_type: str = "raw"
    upload_status: UploadStatus = UploadStatus.UPLOADED
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    ocr_status: OCRStatus = OCRStatus.PROCESSING
    raw_ocr: dict[str, Any] | None = None
    mapped_data: dict[str, Any] | None = None
    error: str | None = None
    file_size: int = Field(default=0, ge=0)
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "documents"
