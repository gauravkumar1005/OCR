from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.dependencies.query import get_document_search_query
from app.dependencies.services import get_document_service
from app.schemas.request import DocumentSearchQuery
from app.schemas.response import (
    APIResponse,
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentResponse,
    DocumentSummaryResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    claimId: str = Form(..., min_length=1),
    documentType: str = Form(default="combined_document"),
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentResponse]:
    return await document_service.upload_document(claimId, file, documentType)


@router.get(
    "",
    response_model=list[DocumentSummaryResponse],
)
async def list_documents(
    filters: DocumentSearchQuery = Depends(get_document_search_query),
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentSummaryResponse]:
    return await document_service.list_documents(filters.claim_id)


@router.get(
    "/{documentId}",
    response_model=APIResponse[DocumentDetailResponse],
)
async def get_document(
    documentId: str,
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentDetailResponse]:
    return await document_service.get_document(documentId)


@router.get(
    "/{documentId}/raw-ocr",
    response_model=APIResponse[dict[str, Any] | None],
)
async def get_raw_ocr(
    documentId: str,
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[dict[str, Any] | None]:
    return await document_service.get_raw_ocr(documentId)


@router.get(
    "/{documentId}/mapped",
    response_model=APIResponse[dict[str, Any] | None],
)
async def get_mapped_data(
    documentId: str,
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[dict[str, Any] | None]:
    return await document_service.get_mapped_data(documentId)


@router.delete(
    "/{documentId}",
    response_model=APIResponse[DeleteDocumentResponse],
)
async def delete_document(
    documentId: str,
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DeleteDocumentResponse]:
    return await document_service.delete_document(documentId)
