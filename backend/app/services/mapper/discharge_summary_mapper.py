from __future__ import annotations

from app.services.mapper.base_mapper import PlaceholderMapper


class DischargeSummaryMapper(PlaceholderMapper):
    document_type = "discharge_summary"
