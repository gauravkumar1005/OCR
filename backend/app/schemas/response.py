from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import OCRStatus, ProcessingStatus, UploadStatus

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API envelope for success responses."""

    model_config = ConfigDict(serialize_by_alias=True)

    success: bool = True
    message: str = "Success"
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "Success") -> "APIResponse[T]":
        return cls(success=True, message=message, data=data)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    document_id: str = Field(alias="documentId")
    claim_id: str = Field(alias="claimId")
    document_type: str | None = Field(default=None, alias="documentType")
    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    cloudinary_url: str = Field(alias="cloudinaryUrl")
    upload_status: UploadStatus = Field(alias="uploadStatus")
    processing_status: ProcessingStatus = Field(alias="processingStatus")
    ocr_status: OCRStatus = Field(alias="ocrStatus")
    error: str | None = None
    file_size: int = Field(alias="fileSize")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class DocumentDetailResponse(DocumentResponse):
    mapped_summary: dict[str, Any] | None = Field(default=None, alias="mappedSummary")


class DocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    document_id: str = Field(alias="documentId")
    document_type: str | None = Field(default=None, alias="documentType")
    processing_status: ProcessingStatus = Field(alias="processingStatus")


class OCRCallbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    document_id: str = Field(alias="documentId")
    ocr_status: OCRStatus = Field(alias="ocrStatus")
    matched_count: int = Field(alias="matchedCount")
    modified_count: int = Field(alias="modifiedCount")


class DeleteDocumentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    document_id: str = Field(alias="documentId")
    deleted: bool = True
