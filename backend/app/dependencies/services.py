from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings
from app.repositories.document_repository import DocumentRepository
from app.services.cloudinary_service import CloudinaryService
from app.services.document_service import DocumentService
from app.services.mapper_service import MapperService
from app.services.ocr_client import OCRClient


class ServiceFactory:
    """Dependency factory helpers."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.document_repository = DocumentRepository()
        self.cloudinary_service = CloudinaryService(self.settings)
        self.ocr_client = OCRClient(self.settings)
        self.mapper_service = MapperService(self.settings)

    def create_document_service(self) -> DocumentService:
        return DocumentService(
            document_repository=self.document_repository,
            cloudinary_service=self.cloudinary_service,
            ocr_client=self.ocr_client,
            mapper_service=self.mapper_service,
            settings=self.settings,
        )


_factory = ServiceFactory()


def get_document_service() -> DocumentService:
    return _factory.create_document_service()
