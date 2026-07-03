from __future__ import annotations

import logging

from app.services.mapper.base_mapper import PlaceholderMapper
from app.services.mapper.claim_form_mapper import ClaimFormMapper
from app.services.mapper.combined_document_mapper import CombinedDocumentMapper
from app.services.mapper.discharge_summary_mapper import DischargeSummaryMapper
from app.services.mapper.field_matcher import FieldMatcher
from app.services.mapper.hospital_bill_mapper import HospitalBillMapper
from app.services.mapper.investigation_report_mapper import InvestigationReportMapper
from app.services.mapper.lab_report_mapper import LabReportMapper
from app.services.mapper.mapping_loader import MappingLoader
from app.services.mapper.prescription_mapper import PrescriptionMapper

logger = logging.getLogger(__name__)


class MapperFactory:
    def __init__(self) -> None:
        self.mapping_loader = MappingLoader()
        self.field_matcher = FieldMatcher()
        self._mappers = {
            "combined_document": CombinedDocumentMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
            "discharge_summary": DischargeSummaryMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
            "investigation_report": InvestigationReportMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
            "hospital_bill": HospitalBillMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
            "prescription": PrescriptionMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
            "claim_form": ClaimFormMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
            "lab_report": LabReportMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher),
        }

    def get_mapper(self, document_type: str | None) -> PlaceholderMapper:
        normalized_document_type = (document_type or "combined_document").strip() or "combined_document"
        mapper = self._mappers.get(normalized_document_type)
        if mapper is not None:
            return mapper
        logger.info("Falling back to placeholder mapper for document_type=%s", normalized_document_type)
        return PlaceholderMapper(mapping_loader=self.mapping_loader, field_matcher=self.field_matcher, document_type=normalized_document_type)
