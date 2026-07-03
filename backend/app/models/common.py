from __future__ import annotations

from enum import Enum


class UploadStatus(str, Enum):
    """File upload lifecycle states."""

    UPLOADED = "UPLOADED"
    FAILED = "FAILED"


class OCRStatus(str, Enum):
    """OCR callback lifecycle states."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    """Processing lifecycle states for OCR and mapping."""

    PENDING = "PENDING"
    OCR_IN_PROGRESS = "OCR_IN_PROGRESS"
    OCR_COMPLETED = "OCR_COMPLETED"
    MAPPING_IN_PROGRESS = "MAPPING_IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
