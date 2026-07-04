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
    page_number: int | None = None
    matched_value: str | None = None


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
            token_records = self._collect_token_records(raw_ocr)

            best = FieldMatchResult()
            page_results: list[FieldMatchResult] = []

            for page_number, page_records in self._group_records_by_page(records).items():
                page_best = self._match_on_page(page_number, page_records, token_records, normalized_labels, hints)
                if page_best.value is not None:
                    page_results.append(page_best)

            if page_results:
                best = max(page_results, key=lambda item: (item.confidence, self._page_rank(item.page_number)))
                self._log_match(best)
                return best

            blob = self._collect_text_blob(records)
            if not blob:
                return best

            for label in normalized_labels:
                pattern = re.compile(rf"{re.escape(label)}\s*[:\-]?\s*([^\n\r|;]+)", re.IGNORECASE)
                match = pattern.search(blob)
                if match:
                    candidate = match.group(1).strip()
                    if candidate and self._looks_like_value(candidate, label):
                        result = FieldMatchResult(
                            value=candidate,
                            confidence=0.6,
                            source_label=label,
                            matched_value=candidate,
                        )
                        self._log_match(result)
                        return result

            return best
        except Exception:
            logger.exception("Field matcher failed")
            return FieldMatchResult()

    def _match_on_page(
        self,
        page_number: int | None,
        page_records: list[dict[str, Any]],
        token_records: list[dict[str, Any]],
        labels: list[str],
        hints: list[str],
    ) -> FieldMatchResult:
        best = FieldMatchResult(page_number=page_number)

        for record in page_records:
            key_text = self.normalize_text(record.get("key"))
            path_text = self.normalize_text(record.get("path"))
            value_text = self.normalize_text(record.get("value"))
            raw_value = self.normalize_value(record.get("value"))
            if raw_value is None:
                continue

            for label in labels:
                score = self._score_match(label, key_text, path_text, value_text, hints)
                if score <= best.confidence or score < 0.55:
                    continue

                if not self._looks_like_value(raw_value, label):
                    nearby = self._find_nearest_value_after_label(label, page_records, token_records, record)
                    if nearby is None:
                        continue
                    candidate_value, candidate_confidence, candidate_source = nearby
                    if candidate_confidence <= score:
                        continue
                    best = FieldMatchResult(
                        value=candidate_value,
                        confidence=candidate_confidence,
                        source_path=candidate_source,
                        source_label=label,
                        page_number=page_number,
                        matched_value=str(candidate_value),
                    )
                    continue

                best = FieldMatchResult(
                    value=raw_value,
                    confidence=score,
                    source_path=record.get("path"),
                    source_label=label,
                    page_number=page_number,
                    matched_value=str(raw_value),
                )

        if best.value is not None:
            return best

        for label in labels:
            nearby = self._find_nearest_value_after_label(label, page_records, token_records, None)
            if nearby is None:
                continue
            candidate_value, candidate_confidence, candidate_source = nearby
            if candidate_value is None or not self._looks_like_value(candidate_value, label):
                continue
            return FieldMatchResult(
                value=candidate_value,
                confidence=candidate_confidence,
                source_path=candidate_source,
                source_label=label,
                page_number=page_number,
                matched_value=str(candidate_value),
            )

        return best

    def _ensure_label_list(self, labels: list[str] | tuple[str, ...] | str) -> list[str]:
        if isinstance(labels, str):
            return [labels]
        return [label for label in labels if label]

    def _iter_records(self, raw_ocr: Any, path: str = "") -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if isinstance(raw_ocr, dict):
            page_number = self._extract_page_number(raw_ocr, path)
            for key, value in raw_ocr.items():
                child_path = f"{path}.{key}" if path else str(key)
                records.extend(self._iter_records(value, child_path))
                if not isinstance(value, (dict, list, tuple)):
                    records.append({"path": child_path, "key": str(key), "value": value, "page_number": page_number})
        elif isinstance(raw_ocr, list):
            page_number = self._extract_page_number(raw_ocr, path)
            for index, value in enumerate(raw_ocr):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                records.extend(self._iter_records(value, child_path))
                if not isinstance(value, (dict, list, tuple)):
                    records.append({"path": child_path, "key": str(index), "value": value, "page_number": page_number})
        return records

    def _collect_token_records(self, raw_ocr: Any) -> list[dict[str, Any]]:
        token_records: list[dict[str, Any]] = []
        pages = self._extract_pages(raw_ocr)
        for page_index, page in enumerate(pages, start=1):
            page_number = self._extract_page_number(page, f"pages[{page_index - 1}]") or page_index
            tokens = self._extract_tokens(page)
            for token_index, token in enumerate(tokens):
                if not isinstance(token, dict):
                    continue
                text = self.normalize_value(token.get("text") or token.get("value") or token.get("word"))
                if text is None:
                    continue
                token_records.append(
                    {
                        "page_number": page_number,
                        "token_index": token_index,
                        "text": str(text),
                        "normalized_text": self.normalize_text(text),
                        "confidence": self._to_float(token.get("confidence"), default=0.0),
                        "x": self._to_float(token.get("x"), default=0.0),
                        "y": self._to_float(token.get("y"), default=0.0),
                        "x2": self._to_float(token.get("x2"), default=0.0),
                        "y2": self._to_float(token.get("y2"), default=0.0),
                        "center_x": self._to_float(token.get("center_x"), default=0.0),
                        "center_y": self._to_float(token.get("center_y"), default=0.0),
                        "path": f"pages[{page_index - 1}].tokens[{token_index}]",
                    }
                )
        return token_records

    def _extract_pages(self, raw_ocr: Any) -> list[dict[str, Any]]:
        if isinstance(raw_ocr, dict):
            pages = raw_ocr.get("pages")
            if isinstance(pages, list):
                return [page for page in pages if isinstance(page, dict)]
        return []

    def _extract_tokens(self, page: dict[str, Any]) -> list[Any]:
        for key in ("tokens", "ocr_data", "indexed_tokens"):
            tokens = page.get(key)
            if isinstance(tokens, list):
                return tokens
        generated = page.get("generated_json")
        if isinstance(generated, dict):
            for key in ("tokens", "ocr_data", "indexed_tokens"):
                tokens = generated.get(key)
                if isinstance(tokens, list):
                    return tokens
        return []

    def _group_records_by_page(self, records: list[dict[str, Any]]) -> dict[int | None, list[dict[str, Any]]]:
        grouped: dict[int | None, list[dict[str, Any]]] = {}
        for record in records:
            page_number = self._extract_page_number(record, record.get("path", ""))
            grouped.setdefault(page_number, []).append(record)
        return grouped

    def _find_nearest_value_after_label(
        self,
        label: str,
        page_records: list[dict[str, Any]],
        token_records: list[dict[str, Any]],
        current_record: dict[str, Any] | None,
    ) -> tuple[Any, float, str | None] | None:
        label_tokens = label.split()
        if not label_tokens:
            return None

        # Prefer structured key/value objects when present.
        for record in page_records:
            key_text = self.normalize_text(record.get("key"))
            path_text = self.normalize_text(record.get("path"))
            value = self.normalize_value(record.get("value"))
            if value is None:
                continue
            if self._label_matches(key_text, path_text, label):
                if self._looks_like_value(value, label):
                    confidence = min(0.95, self._score_match(label, key_text, path_text, self.normalize_text(value), []))
                    return value, max(confidence, 0.8), record.get("path")

        # Token-based fallback: choose the nearest value to the right or below the label.
        label_token = None
        if current_record is not None:
            label_token = self._find_label_token(label, token_records, current_record)
        if label_token is None:
            label_token = self._find_label_token(label, token_records, None)
        if label_token is None:
            return None

        candidates = self._rank_value_candidates(label, label_token, token_records)
        if not candidates:
            return None
        return candidates[0]

    def _find_label_token(
        self,
        label: str,
        token_records: list[dict[str, Any]],
        current_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        normalized_label = self.normalize_text(label)
        if not normalized_label:
            return None

        current_page = current_record.get("page_number") if current_record else None
        current_path = current_record.get("path") if current_record else None
        for token in token_records:
            if current_page is not None and token.get("page_number") != current_page:
                continue
            token_text = token.get("normalized_text", "")
            if token_text == normalized_label or self._label_matches(token_text, token_text, normalized_label):
                if current_path and token.get("path") == current_path:
                    continue
                return token
        best_token = None
        best_score = 0.0
        for token in token_records:
            if current_page is not None and token.get("page_number") != current_page:
                continue
            score = self._token_label_score(normalized_label, token.get("normalized_text", ""))
            if score > best_score:
                best_score = score
                best_token = token
        return best_token if best_score >= 0.75 else None

    def _rank_value_candidates(
        self,
        label: str,
        label_token: dict[str, Any],
        token_records: list[dict[str, Any]],
    ) -> list[tuple[Any, float, str | None]]:
        label_page = label_token.get("page_number")
        label_x = self._to_float(label_token.get("x"), default=0.0)
        label_y = self._to_float(label_token.get("y"), default=0.0)
        label_x2 = self._to_float(label_token.get("x2"), default=label_x)
        label_y2 = self._to_float(label_token.get("y2"), default=label_y)
        label_center_y = self._to_float(label_token.get("center_y"), default=label_y)

        candidates: list[tuple[Any, float, str | None]] = []
        for token in token_records:
            if label_page is not None and token.get("page_number") != label_page:
                continue
            token_text = token.get("normalized_text", "")
            if not token_text or self._label_matches(token_text, token_text, label):
                continue
            if self._looks_like_label(token.get("text"), label):
                continue

            token_x = self._to_float(token.get("x"), default=0.0)
            token_y = self._to_float(token.get("y"), default=0.0)
            token_center_y = self._to_float(token.get("center_y"), default=token_y)
            token_confidence = self._to_float(token.get("confidence"), default=0.0)

            is_right = token_x >= label_x2 - 8
            is_below = token_y >= label_y - 4 and abs(token_center_y - label_center_y) <= 40
            distance = self._horizontal_distance(label_x2, token_x) + self._vertical_distance(label_center_y, token_center_y)

            if not is_right and not is_below:
                continue

            value = self.normalize_value(token.get("text") or token.get("value"))
            if value is None or not self._looks_like_value(value, label):
                continue

            confidence = min(0.99, 0.55 + (0.1 if is_right else 0.05) + token_confidence * 0.25 + max(0.0, 0.2 - distance / 1200))
            candidates.append((value, confidence, token.get("path")))

        candidates.sort(key=lambda item: (-item[1], str(item[0])))
        return candidates

    def _label_matches(self, text_a: str, text_b: str, label: str) -> bool:
        if not text_a or not label:
            return False
        compact_label = label.replace(" ", "")
        compact_a = text_a.replace(" ", "")
        compact_b = text_b.replace(" ", "")
        return compact_label == compact_a or compact_label == compact_b or compact_label in compact_a or compact_label in compact_b

    def _looks_like_label(self, candidate: Any, label: str) -> bool:
        candidate_text = self.normalize_text(candidate)
        label_text = self.normalize_text(label)
        if not candidate_text:
            return False
        if candidate_text == label_text:
            return True
        if candidate_text.replace(" ", "") == label_text.replace(" ", ""):
            return True
        return SequenceMatcher(None, candidate_text, label_text).ratio() >= 0.93

    def _looks_like_value(self, candidate: Any, label: str) -> bool:
        candidate_text = self.normalize_text(candidate)
        label_text = self.normalize_text(label)
        if not candidate_text:
            return False
        if candidate_text == label_text:
            return False
        if candidate_text.replace(" ", "") == label_text.replace(" ", ""):
            return False
        if SequenceMatcher(None, candidate_text, label_text).ratio() >= 0.93:
            return False
        if candidate_text in {"na", "n a", "none", "null", "unknown", "not available"}:
            return False
        return True

    def _token_label_score(self, label: str, token_text: str) -> float:
        if not label or not token_text:
            return 0.0
        label_tokens = label.split()
        token_tokens = token_text.split()
        if not label_tokens or not token_tokens:
            return 0.0
        overlap = len(set(label_tokens) & set(token_tokens)) / max(len(set(label_tokens)), 1)
        similarity = SequenceMatcher(None, label, token_text).ratio()
        score = max(similarity, overlap)
        if label.replace(" ", "") == token_text.replace(" ", ""):
            score = 1.0
        return score

    def _horizontal_distance(self, label_x2: float, token_x: float) -> float:
        return max(0.0, token_x - label_x2)

    def _vertical_distance(self, label_y: float, token_y: float) -> float:
        return abs(token_y - label_y)

    def _extract_page_number(self, item: Any, path: str = "") -> int | None:
        if isinstance(item, dict):
            for key in ("page_number", "pageNumber", "page", "page_index"):
                value = item.get(key)
                if isinstance(value, int):
                    return value
                if isinstance(value, str) and value.isdigit():
                    return int(value)
            generated = item.get("generated_json")
            if isinstance(generated, dict):
                for key in ("page_number", "pageNumber", "page", "page_index"):
                    value = generated.get(key)
                    if isinstance(value, int):
                        return value
                    if isinstance(value, str) and value.isdigit():
                        return int(value)
        match = re.search(r"pages?\[(\d+)\]", path)
        if match:
            return int(match.group(1)) + 1
        match = re.search(r"page[_\s-]?(\d+)", path, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _page_rank(self, page_number: int | None) -> float:
        if page_number is None:
            return 0.0
        return 1.0 / (1.0 + max(page_number - 1, 0) * 0.02)

    def _to_float(self, value: Any, *, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _log_match(self, result: FieldMatchResult) -> None:
        if result.value is None:
            return
        logger.info(
            "Matched Label=%s Matched Value=%s Page Number=%s Confidence=%.2f Source Path=%s",
            result.source_label,
            result.matched_value if result.matched_value is not None else result.value,
            result.page_number,
            result.confidence,
            result.source_path,
        )

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
