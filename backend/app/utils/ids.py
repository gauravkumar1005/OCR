from __future__ import annotations

from bson import ObjectId


def is_valid_object_id(value: str) -> bool:
    return ObjectId.is_valid(value)

