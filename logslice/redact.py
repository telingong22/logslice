"""Field redaction utilities for logslice."""

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional

_MASK = "***"


def redact_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Replace the values of specified top-level fields with a mask."""
    out = dict(record)
    for field in fields:
        if field in out:
            out[field] = _MASK
    return out


def redact_pattern(
    record: Dict[str, Any],
    pattern: str,
    replacement: str = _MASK,
) -> Dict[str, Any]:
    """Replace substrings matching *pattern* in all string values."""
    rx = re.compile(pattern)
    out = {}
    for k, v in record.items():
        if isinstance(v, str):
            out[k] = rx.sub(replacement, v)
        else:
            out[k] = v
    return out


def redact_nested(
    record: Dict[str, Any],
    path: str,
    sep: str = ".",
) -> Dict[str, Any]:
    """Redact a nested field identified by a dot-separated *path*."""
    keys = path.split(sep)
    out = _deep_copy(record)
    node = out
    for key in keys[:-1]:
        if not isinstance(node.get(key), dict):
            return out
        node = node[key]
    if keys[-1] in node:
        node[keys[-1]] = _MASK
    return out


def _deep_copy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(i) for i in obj]
    return obj


def apply_redactions(
    records: Iterable[Dict[str, Any]],
    fields: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    nested_paths: Optional[List[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """Apply all configured redactions to each record in *records*."""
    for record in records:
        if fields:
            record = redact_fields(record, fields)
        if pattern:
            record = redact_pattern(record, pattern)
        if nested_paths:
            for path in nested_paths:
                record = redact_nested(record, path)
        yield record
