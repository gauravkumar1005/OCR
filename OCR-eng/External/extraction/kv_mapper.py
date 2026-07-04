from __future__ import annotations

from typing import Any

from .spatial_utils import group_tokens_into_rows


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def map_key_values(indexed_tokens: list[dict[str, Any]], page: int | None = None) -> list[dict[str, Any]]:
    """Best-effort legacy compatibility mapper.

    The merge engine expects a list of key/value-like dictionaries. This keeps
    the structure stable without changing the downstream OCR pipeline wiring.
    """
    rows = group_tokens_into_rows(indexed_tokens)
    kv_pairs: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows, start=1):
        row_tokens = sorted(row, key=lambda token: token.get("x", 0))
        row_texts = [_normalize_text(str(token.get("text", ""))) for token in row_tokens]
        row_texts = [text for text in row_texts if text]
        if not row_texts:
            continue

        if len(row_texts) == 1:
            field = row_texts[0]
            value = ""
        else:
            field = row_texts[0].rstrip(":")
            value = " ".join(row_texts[1:]).lstrip(":").strip()

        kv_pairs.append(
            {
                "field": field,
                "value": value,
                "page": page,
                "row": row_index,
                "confidence": max(
                    (
                        float(token.get("confidence", token.get("conf", 0)) or 0)
                        for token in row_tokens
                    ),
                    default=0.0,
                ),
                "tokens": row_tokens,
            }
        )

    return kv_pairs
