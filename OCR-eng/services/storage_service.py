from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, temp_root: Path) -> None:
        self.temp_root = temp_root
        self.input_root = temp_root / "input"
        self.output_root = temp_root / "output"

    def prepare_job_directories(self, document_id: str) -> dict[str, Path]:
        document_root = self.output_root / document_id
        image_root = document_root / "images"
        json_root = document_root / "json"
        self.input_root.mkdir(parents=True, exist_ok=True)
        image_root.mkdir(parents=True, exist_ok=True)
        json_root.mkdir(parents=True, exist_ok=True)
        return {
            "document_root": document_root,
            "image_root": image_root,
            "json_root": json_root,
        }

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("JSON saved to %s", path)
