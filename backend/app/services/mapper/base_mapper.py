from __future__ import annotations

import logging
from abc import ABC
from datetime import datetime, timezone
from typing import Any

from app.exceptions.base import MapperConfigurationException
from app.services.mapper.field_matcher import FieldMatcher
from app.services.mapper.mapping_loader import MappingLoader

logger = logging.getLogger(__name__)


class BaseMapper(ABC):
    document_type = "combined_document"

    def __init__(self, *, mapping_loader: MappingLoader | None = None, field_matcher: FieldMatcher | None = None) -> None:
        self.mapping_loader = mapping_loader or MappingLoader()
        self.field_matcher = field_matcher or FieldMatcher()

    def map(self, raw_ocr: dict[str, Any] | None, document_type: str | None = None) -> dict[str, Any]:
        normalized_document_type = (document_type or self.document_type or "combined_document").strip() or "combined_document"
        payload = raw_ocr or {}

        mapping = self.load_mapping(normalized_document_type)
        try:
            return self._map_with_config(payload, mapping, normalized_document_type)
        except Exception:
            logger.exception("Mapper failed for document_type=%s", normalized_document_type)
            return self._empty_result(payload, normalized_document_type)

    def load_mapping(self, document_type: str | None = None) -> dict[str, Any]:
        normalized_document_type = (document_type or self.document_type or "combined_document").strip() or "combined_document"
        return self.mapping_loader.load(normalized_document_type)

    def extract_field(
        self,
        raw_ocr: dict[str, Any],
        field_config: Any,
        *,
        field_name: str | None = None,
    ) -> Any | None:
        labels, hints = self._resolve_field_config(field_config)
        match = self.field_matcher.match_field(raw_ocr, labels, value_hint_patterns=hints)
        if match.value is None:
            logger.info("Missing field name=%s", field_name or labels[0] if labels else "<unknown>")
        else:
            logger.info(
                "Matched field name=%s confidence=%.2f",
                field_name or labels[0] if labels else "<unknown>",
                match.confidence,
            )
        return self.normalize_value(match.value)

    def extract_section(
        self,
        raw_ocr: dict[str, Any],
        section_config: Any,
        *,
        section_name: str | None = None,
    ) -> dict[str, Any]:
        if not section_config:
            return {}
        field_map = self._resolve_section_config(section_config)
        extracted: dict[str, Any] = {}
        for field_name, field_config in field_map.items():
            extracted[field_name] = self.extract_field(raw_ocr, field_config, field_name=field_name)
        logger.info("Extracted section name=%s fields=%s", section_name or "<unknown>", sorted(extracted.keys()))
        return extracted

    def extract_tables(self, raw_ocr: dict[str, Any], table_config: Any) -> list[dict[str, Any]]:
        if not table_config:
            return []

        table_items = table_config if isinstance(table_config, list) else [table_config]
        tables: list[dict[str, Any]] = []
        for index, table_item in enumerate(table_items, start=1):
            if not isinstance(table_item, dict):
                continue
            table_name = str(table_item.get("name") or table_item.get("tableName") or f"table_{index}")
            field_map = self._resolve_section_config(table_item.get("fields") or table_item)
            rows = {
                field_name: self.extract_field(raw_ocr, field_config, field_name=field_name)
                for field_name, field_config in field_map.items()
            }
            tables.append({"name": table_name, "rows": rows})
            logger.info("Extracted table name=%s fields=%s", table_name, sorted(rows.keys()))
        return tables

    def normalize_value(self, value: Any) -> Any | None:
        return self.field_matcher.normalize_value(value)

    def _map_with_config(self, raw_ocr: dict[str, Any], mapping: dict[str, Any], document_type: str) -> dict[str, Any]:
        summary_config = mapping.get("summary") or {}
        section_config = mapping.get("sections") or {}
        table_config = mapping.get("tables") or []

        summary = self.extract_section(raw_ocr, summary_config, section_name="summary")
        if isinstance(summary_config, dict):
            summary = {key: summary.get(key) for key in summary_config.keys()}
        summary["documentType"] = document_type

        sections = self._extract_sections(raw_ocr, section_config)
        tables = self.extract_tables(raw_ocr, table_config)

        return {
            "summary": summary,
            "sections": sections,
            "tables": tables,
            "metadata": {
                "pageCount": self._extract_page_count(raw_ocr),
                "processedAt": self._now_iso(),
            },
        }

    def _extract_sections(self, raw_ocr: dict[str, Any], section_config: Any) -> list[dict[str, Any]]:
        if not section_config:
            return []
        if isinstance(section_config, dict) and "fields" in section_config:
            return [self.extract_section(raw_ocr, section_config, section_name=str(section_config.get("name") or "section"))]
        if isinstance(section_config, dict):
            sections: list[dict[str, Any]] = []
            for section_name, config in section_config.items():
                sections.append({"name": section_name, "fields": self.extract_section(raw_ocr, config, section_name=str(section_name))})
            return sections
        if isinstance(section_config, list):
            sections: list[dict[str, Any]] = []
            for index, config in enumerate(section_config, start=1):
                if not isinstance(config, dict):
                    continue
                section_name = str(config.get("name") or config.get("sectionName") or f"section_{index}")
                sections.append({"name": section_name, "fields": self.extract_section(raw_ocr, config.get("fields") or config, section_name=section_name)})
            return sections
        return []

    def _resolve_field_config(self, field_config: Any) -> tuple[list[str], list[str]]:
        if isinstance(field_config, dict):
            keywords = field_config.get("keywords") or field_config.get("labels") or field_config.get("terms") or []
            hints = field_config.get("hints") or field_config.get("valueHints") or []
            return self._as_list(keywords), self._as_list(hints)
        if isinstance(field_config, (list, tuple, set)):
            return self._as_list(field_config), []
        if field_config is None:
            return [], []
        return [str(field_config)], []

    def _resolve_section_config(self, section_config: Any) -> dict[str, Any]:
        if isinstance(section_config, dict) and "fields" in section_config and isinstance(section_config["fields"], dict):
            return section_config["fields"]
        if isinstance(section_config, dict):
            return section_config
        return {}

    def _as_list(self, value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item is not None and str(item).strip()]
        if value is None:
            return []
        return [str(value)]

    def _empty_result(self, raw_ocr: dict[str, Any], document_type: str) -> dict[str, Any]:
        return {
            "summary": {"documentType": document_type},
            "sections": [],
            "tables": [],
            "metadata": {
                "pageCount": self._extract_page_count(raw_ocr),
                "processedAt": self._now_iso(),
            },
        }

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _extract_page_count(self, raw_ocr: dict[str, Any]) -> int:
        if not isinstance(raw_ocr, dict):
            return 0
        page_count = raw_ocr.get("page_count")
        if isinstance(page_count, int):
            return page_count
        pages = raw_ocr.get("pages")
        if isinstance(pages, list):
            return len(pages)
        return 0


class PlaceholderMapper(BaseMapper):
    document_type = "combined_document"

    def __init__(self, *, mapping_loader: MappingLoader | None = None, field_matcher: FieldMatcher | None = None, document_type: str | None = None) -> None:
        super().__init__(mapping_loader=mapping_loader, field_matcher=field_matcher)
        if document_type:
            self.document_type = document_type

    def _map_with_config(self, raw_ocr: dict[str, Any], mapping: dict[str, Any], document_type: str) -> dict[str, Any]:
        logger.info("Using placeholder mapper for document_type=%s", document_type)
        return super()._map_with_config(raw_ocr, mapping, document_type)
