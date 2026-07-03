from __future__ import annotations

from app.services.mapper.base_mapper import PlaceholderMapper


class PrescriptionMapper(PlaceholderMapper):
    document_type = "prescription"
