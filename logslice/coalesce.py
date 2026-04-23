"""Field coalescing: return the first non-null value across a list of fields."""

from typing import Any, Dict, Iterable, List, Optional


def _get(record: Dict[str, Any], field: str) -> Optional[Any]:
    """Return value for field, or None if missing or explicitly None."""
    value = record.get(field)
    return value if value is not None else None


def coalesce_fields(
    record: Dict[str, Any],
    fields: List[str],
    target: str,
    default: Optional[Any] = None,
) -> Dict[str, Any]:
    """Add *target* to a copy of *record* with the first non-None value from *fields*.

    If all fields are absent or None, *default* is used.
    The original record is not mutated.
    """
    result = dict(record)
    for field in fields:
        value = _get(record, field)
        if value is not None:
            result[target] = value
            return result
    result[target] = default
    return result


def coalesce_records(
    records: Iterable[Dict[str, Any]],
    fields: List[str],
    target: str,
    default: Optional[Any] = None,
) -> Iterable[Dict[str, Any]]:
    """Apply :func:`coalesce_fields` to every record in *records*."""
    for record in records:
        yield coalesce_fields(record, fields, target, default)


def fill_missing(
    record: Dict[str, Any],
    field: str,
    fallback_fields: List[str],
    default: Optional[Any] = None,
) -> Dict[str, Any]:
    """If *field* is absent or None in *record*, fill it from *fallback_fields*.

    Unlike :func:`coalesce_fields`, the target key is *field* itself so the
    record is "filled in" rather than producing a new key.
    """
    if _get(record, field) is not None:
        return dict(record)
    return coalesce_fields(record, fallback_fields, field, default)


def apply_coalesce(
    records: Iterable[Dict[str, Any]],
    specs: List[Dict[str, Any]],
) -> Iterable[Dict[str, Any]]:
    """Apply a list of coalesce specs to each record.

    Each spec is a dict with keys:
      - fields  (list[str])        — source fields to try in order
      - target  (str)              — destination field name
      - default (any, optional)    — fallback value (default None)
    """
    for record in records:
        for spec in specs:
            record = coalesce_fields(
                record,
                spec["fields"],
                spec["target"],
                spec.get("default"),
            )
        yield record
