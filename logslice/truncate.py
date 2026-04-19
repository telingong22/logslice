"""Field value truncation utilities for logslice."""

from typing import Any, Dict, Iterable, Iterator, List, Optional


def truncate_value(value: Any, max_length: int, suffix: str = "...") -> Any:
    """Truncate a string value to max_length, appending suffix if truncated."""
    if not isinstance(value, str):
        return value
    if len(value) <= max_length:
        return value
    cut = max(0, max_length - len(suffix))
    return value[:cut] + suffix


def truncate_fields(
    record: Dict[str, Any],
    fields: List[str],
    max_length: int,
    suffix: str = "...",
) -> Dict[str, Any]:
    """Return a new record with specified fields truncated."""
    result = dict(record)
    for field in fields:
        if field in result:
            result[field] = truncate_value(result[field], max_length, suffix)
    return result


def truncate_all(
    record: Dict[str, Any],
    max_length: int,
    suffix: str = "...",
    skip: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Return a new record with all string fields truncated."""
    skip_set = set(skip or [])
    result = {}
    for key, value in record.items():
        if key in skip_set:
            result[key] = value
        else:
            result[key] = truncate_value(value, max_length, suffix)
    return result


def apply_truncation(
    records: Iterable[Dict[str, Any]],
    fields: Optional[List[str]] = None,
    max_length: int = 80,
    suffix: str = "...",
    skip: Optional[List[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """Apply truncation to an iterable of records.

    If fields is given, only those fields are truncated.
    Otherwise all string fields are truncated (respecting skip list).
    """
    for record in records:
        if fields is not None:
            yield truncate_fields(record, fields, max_length, suffix)
        else:
            yield truncate_all(record, max_length, suffix, skip)
