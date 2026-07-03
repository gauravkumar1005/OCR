from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.exceptions.base import MapperConfigurationException

logger = logging.getLogger(__name__)


class MappingLoader:
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path(__file__).resolve().parents[2] / "config" / "mapping"

    def load(self, document_type: str | None) -> dict[str, Any]:
        normalized_document_type = (document_type or "combined_document").strip() or "combined_document"
        mapping_path = self.base_path / f"{normalized_document_type}.json"
        if not mapping_path.exists():
            raise MapperConfigurationException(
                f"Mapping config not found for document_type='{normalized_document_type}' at '{mapping_path}'"
            )

        return self._load_json(mapping_path)

    @lru_cache(maxsize=64)
    def _load_json(self, mapping_path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(mapping_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise MapperConfigurationException(f"Mapping config missing: {mapping_path}") from exc
        except json.JSONDecodeError as exc:
            raise MapperConfigurationException(f"Invalid JSON in mapping config: {mapping_path}") from exc

        if not isinstance(payload, dict):
            raise MapperConfigurationException(f"Mapping config must be a JSON object: {mapping_path}")

        logger.info("Loaded mapping file: %s", mapping_path)
        return payload
