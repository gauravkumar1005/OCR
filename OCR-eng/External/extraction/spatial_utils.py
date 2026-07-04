from __future__ import annotations

from OCR_Extraction_folder.table_grid_detector import group_cells_into_rows


def group_tokens_into_rows(tokens, y_threshold: int = 25):
    """Backwards-compatible row grouping for OCR tokens."""
    return group_cells_into_rows(tokens, y_threshold=y_threshold)
