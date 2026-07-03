from __future__ import annotations

from app.services.mapper.base_mapper import PlaceholderMapper


class HospitalBillMapper(PlaceholderMapper):
    document_type = "hospital_bill"
