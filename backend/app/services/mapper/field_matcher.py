from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FieldMatchResult:
    value: Any | None = None
    confidence: float = 0.0
    source_path: str | None = None
    source_label: str | None = None


class FieldMatcher:
    def normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).lower().strip()
        text = text.replace("_", " ").replace("-", " ")
        text = re.sub(r"[^a-z0-9\s]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def normalize_value(self, value: Any) -> Any | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        if isinstance(value, (int, float, bool)):
            return value
        return str(value).strip() or None

    def match_field(
        self,
        raw_ocr: Any,
        labels: list[str] | tuple[str, ...] | str,
        *,
        value_hint_patterns: list[str] | tuple[str, ...] | None = None,
    ) -> FieldMatchResult:
        try:
            normalized_labels = self._ensure_label_list(labels)
            hints = [self.normalize_text(pattern) for pattern in (value_hint_patterns or []) if pattern]
            records = self._iter_records(raw_ocr)
            best = FieldMatchResult()

            for record in records:
                key_text = self.normalize_text(record.get("key"))
                path_text = self.normalize_text(record.get("path"))
                value_text = self.normalize_text(record.get("value"))
                raw_value = self.normalize_value(record.get("value"))
                if raw_value is None:
                    continue

                for label in normalized_labels:
                    score = self._score_match(label, key_text, path_text, value_text, hints)
                    if score > best.confidence and score >= 0.55:
                        best = FieldMatchResult(
                            value=raw_value,
                            confidence=score,
                            source_path=record.get("path"),
                            source_label=label,
                        )

            if best.value is not None:
                logger.info(
                    "Matched field label=%s source_path=%s confidence=%.2f",
                    best.source_label,
                    best.source_path,
                    best.confidence,
                )
                return best

            blob = self._collect_text_blob(records)
            if not blob:
                return best

            for label in normalized_labels:
                pattern = re.compile(rf"{re.escape(label)}\s*[:\-]?\s*([^\n\r|;]+)", re.IGNORECASE)
                match = pattern.search(blob)
                if match:
                    candidate = match.group(1).strip()
                    if candidate:
                        return FieldMatchResult(value=candidate, confidence=0.6, source_label=label)

            return best
        except Exception:
            logger.exception("Field matcher failed")
            return FieldMatchResult()

    def _ensure_label_list(self, labels: list[str] | tuple[str, ...] | str) -> list[str]:
        if isinstance(labels, str):
            return [labels]
        return [label for label in labels if label]

    def _iter_records(self, raw_ocr: Any, path: str = "") -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if isinstance(raw_ocr, dict):
            for key, value in raw_ocr.items():
                child_path = f"{path}.{key}" if path else str(key)
                records.extend(self._iter_records(value, child_path))
                if not isinstance(value, (dict, list, tuple)):
                    records.append({"path": child_path, "key": str(key), "value": value})
        elif isinstance(raw_ocr, list):
            for index, value in enumerate(raw_ocr):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                records.extend(self._iter_records(value, child_path))
                if not isinstance(value, (dict, list, tuple)):
                    records.append({"path": child_path, "key": str(index), "value": value})
        return records

    def _collect_text_blob(self, records: list[dict[str, Any]]) -> str:
        texts: list[str] = []
        for record in records:
            value = self.normalize_value(record.get("value"))
            if value is not None:
                texts.append(str(value))
        return "\n".join(texts)

    def _score_match(
        self,
        label: str,
        key_text: str,
        path_text: str,
        value_text: str,
        hints: list[str],
    ) -> float:
        if not label:
            return 0.0

        label_compact = label.replace(" ", "")
        key_compact = key_text.replace(" ", "")
        path_compact = path_text.replace(" ", "")
        value_compact = value_text.replace(" ", "")

        similarity = max(
            SequenceMatcher(None, label, key_text).ratio(),
            SequenceMatcher(None, label, path_text).ratio(),
            SequenceMatcher(None, label, value_text).ratio(),
            SequenceMatcher(None, label_compact, key_compact).ratio(),
            SequenceMatcher(None, label_compact, path_compact).ratio(),
            SequenceMatcher(None, label_compact, value_compact).ratio(),
        )

        if label_compact and (label_compact in key_compact or label_compact in path_compact or label_compact in value_compact):
            similarity = max(similarity, 0.98)
        if any(token in key_text.split() or token in path_text.split() or token in value_text.split() for token in label.split() if token):
            similarity = max(similarity, 0.85)
        if hints and any(hint and hint in value_text for hint in hints):
            similarity = max(similarity, 0.9)

        return similarity
