"""Utilities for flattening nested log records into dot-notation keys."""

from typing import Any, Dict, Iterator, Optional


def _flatten_dict(
    obj: Any,
    prefix: str = "",
    sep: str = ".",
    max_depth: Optional[int] = None,
    _depth: int = 0,
) -> Iterator[tuple]:
    """Recursively yield (key, value) pairs with dot-notation keys."""
    if isinstance(obj, dict) and (max_depth is None or _depth < max_depth):
        for k, v in obj.items():
            full_key = f"{prefix}{sep}{k}" if prefix else k
            yield from _flatten_dict(v, full_key, sep, max_depth, _depth + 1)
    else:
        yield (prefix, obj)


def flatten_record(
    record: Dict[str, Any],
    sep: str = ".",
    max_depth: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a new record with all nested dicts flattened to dot-notation keys.

    Args:
        record: The log record dict to flatten.
        sep: Separator to use between key segments. Defaults to '.'.
        max_depth: Maximum nesting depth to flatten. None means unlimited.

    Returns:
        A new flat dict.
    """
    return dict(_flatten_dict(record, sep=sep, max_depth=max_depth))


def unflatten_record(
    record: Dict[str, Any],
    sep: str = ".",
) -> Dict[str, Any]:
    """Reconstruct a nested dict from a flat dot-notation record.

    Args:
        record: Flat dict with dot-notation keys.
        sep: Separator used between key segments.

    Returns:
        A nested dict.
    """
    result: Dict[str, Any] = {}
    for key, value in record.items():
        parts = key.split(sep)
        node = result
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
    return result
