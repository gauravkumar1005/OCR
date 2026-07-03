from __future__ import annotations

from app.services.mapper.base_mapper import BaseMapper


class CombinedDocumentMapper(BaseMapper):
    document_type = "combined_document"
