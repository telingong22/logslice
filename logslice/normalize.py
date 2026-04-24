"""Field value normalization: case folding, stripping, type coercion."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


def normalize_case(record: Dict[str, Any], fields: List[str], mode: str = "lower") -> Dict[str, Any]:
    """Return a copy of record with string fields case-folded.

    mode: 'lower' | 'upper' | 'title'
    """
    if mode not in ("lower", "upper", "title"):
        raise ValueError(f"Unknown mode {mode!r}; expected 'lower', 'upper', or 'title'")
    out = dict(record)
    for field in fields:
        if field in out and isinstance(out[field], str):
            out[field] = getattr(out[field], mode)()
    return out


def normalize_strip(record: Dict[str, Any], fields: List[str], chars: Optional[str] = None) -> Dict[str, Any]:
    """Return a copy of record with leading/trailing chars stripped from string fields."""
    out = dict(record)
    for field in fields:
        if field in out and isinstance(out[field], str):
            out[field] = out[field].strip(chars)
    return out


def normalize_coerce(record: Dict[str, Any], type_map: Dict[str, str]) -> Dict[str, Any]:
    """Return a copy of record with fields coerced to the specified types.

    type_map values: 'int' | 'float' | 'bool' | 'str'
    Values that cannot be coerced are left unchanged.
    """
    _coercers = {
        "int": int,
        "float": float,
        "str": str,
        "bool": lambda v: v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes"),
    }
    out = dict(record)
    for field, typename in type_map.items():
        if field not in out:
            continue
        coerce = _coercers.get(typename)
        if coerce is None:
            raise ValueError(f"Unknown type {typename!r}")
        try:
            out[field] = coerce(out[field])
        except (ValueError, TypeError):
            pass
    return out


def apply_normalizations(
    records: Iterable[Dict[str, Any]],
    case_fields: Optional[List[str]] = None,
    case_mode: str = "lower",
    strip_fields: Optional[List[str]] = None,
    strip_chars: Optional[str] = None,
    type_map: Optional[Dict[str, str]] = None,
) -> Iterator[Dict[str, Any]]:
    """Apply a chain of normalizations to each record in the stream."""
    for record in records:
        if case_fields:
            record = normalize_case(record, case_fields, mode=case_mode)
        if strip_fields:
            record = normalize_strip(record, strip_fields, chars=strip_chars)
        if type_map:
            record = normalize_coerce(record, type_map)
        yield record
