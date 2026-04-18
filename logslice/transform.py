"""Field transformation and renaming utilities for logslice."""

from typing import Any, Dict, List, Optional


def rename_fields(record: Dict[str, Any], renames: Dict[str, str]) -> Dict[str, Any]:
    """Return a copy of record with fields renamed according to the mapping."""
    result = {}
    for key, value in record.items():
        new_key = renames.get(key, key)
        result[new_key] = value
    return result


def drop_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Return a copy of record with specified fields removed."""
    return {k: v for k, v in record.items() if k not in fields}


def keep_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Return a copy of record with only the specified fields retained."""
    return {k: v for k, v in record.items() if k in fields}


def add_field(record: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """Return a copy of record with a new field added or overwritten."""
    result = dict(record)
    result[key] = value
    return result


def apply_transforms(
    records,
    renames: Optional[Dict[str, str]] = None,
    drop: Optional[List[str]] = None,
    keep: Optional[List[str]] = None,
):
    """Generator that applies a chain of transforms to each record."""
    for record in records:
        if renames:
            record = rename_fields(record, renames)
        if drop:
            record = drop_fields(record, drop)
        if keep:
            record = keep_fields(record, keep)
        yield record
