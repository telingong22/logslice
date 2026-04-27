"""Field masking: partially obscure field values while preserving structure."""

import re
from typing import Any, Dict, Iterable, List, Optional


def _get(record: Dict, field: str) -> Any:
    """Return value at dotted field path or None."""
    parts = field.split(".")
    cur = record
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def _set(record: Dict, field: str, value: Any) -> None:
    """Set value at dotted field path in-place."""
    parts = field.split(".")
    cur = record
    for p in parts[:-1]:
        if not isinstance(cur.get(p), dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def mask_field(
    record: Dict,
    field: str,
    *,
    show_first: int = 0,
    show_last: int = 0,
    mask_char: str = "*",
) -> Dict:
    """Return a copy of *record* with *field* partially masked.

    Characters beyond *show_first* from the start and *show_last* from the
    end are replaced with *mask_char*.  If the value is not a string it is
    converted to one before masking.
    """
    value = _get(record, field)
    if value is None:
        return dict(record)
    s = str(value)
    n = len(s)
    first = max(0, min(show_first, n))
    last = max(0, min(show_last, n - first))
    hidden = max(0, n - first - last)
    masked = s[:first] + mask_char * hidden + s[n - last :] if last else s[:first] + mask_char * hidden
    result = dict(record)
    _set(result, field, masked)
    return result


def mask_pattern(
    record: Dict,
    pattern: str,
    replacement: str = "***",
) -> Dict:
    """Return a copy of *record* with all string values matching *pattern* replaced."""
    rx = re.compile(pattern)

    def _process(v: Any) -> Any:
        if isinstance(v, str):
            return rx.sub(replacement, v)
        if isinstance(v, dict):
            return {k: _process(vv) for k, vv in v.items()}
        if isinstance(v, list):
            return [_process(i) for i in v]
        return v

    return _process(dict(record))  # type: ignore[return-value]


def apply_masks(
    records: Iterable[Dict],
    fields: Optional[List[str]] = None,
    *,
    show_first: int = 0,
    show_last: int = 0,
    mask_char: str = "*",
    pattern: Optional[str] = None,
    replacement: str = "***",
) -> Iterable[Dict]:
    """Apply masking to an iterable of records."""
    for record in records:
        r = record
        if fields:
            for f in fields:
                r = mask_field(r, f, show_first=show_first, show_last=show_last, mask_char=mask_char)
        if pattern:
            r = mask_pattern(r, pattern, replacement)
        yield r
