from __future__ import annotations

from fastapi import Query

from app.schemas.request import DocumentSearchQuery


async def get_document_search_query(
    claimId: str = Query(..., min_length=1),
) -> DocumentSearchQuery:
    return DocumentSearchQuery(claimId=claimId)
