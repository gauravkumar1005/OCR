from __future__ import annotations

import re
from typing import Any


def _normalize_label(label: str) -> str:
    normalized = label.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def normalize_kv_pairs(kv_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compatibility normalizer used by the OCR merge engine."""
    normalized_pairs: list[dict[str, Any]] = []

    for kv in kv_pairs:
        field = str(kv.get("field", "")).strip()
        value = kv.get("value", "")
        normalized_pairs.append(
            {
                **kv,
                "normalized_label": _normalize_label(field),
                "normalized_value": value,
            }
        )

    return normalized_pairs
