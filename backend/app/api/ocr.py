from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.services import get_document_service
from app.schemas.request import OCRCallbackRequest
from app.schemas.response import APIResponse, OCRCallbackResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post("/callback", response_model=APIResponse[OCRCallbackResponse])
@router.patch("/callback", response_model=APIResponse[OCRCallbackResponse])
async def ocr_callback(
    payload: OCRCallbackRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[OCRCallbackResponse]:
    return await document_service.handle_ocr_callback(payload)
