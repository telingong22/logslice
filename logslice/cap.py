"""Cap numeric field values to a minimum and/or maximum bound."""

from typing import Any, Dict, Iterable, Iterator, List, Optional


def _get(record: Dict[str, Any], field: str) -> Any:
    """Return the value at *field*, supporting dot-notation for nested keys."""
    parts = field.split(".")
    val = record
    for part in parts:
        if not isinstance(val, dict):
            return None
        val = val.get(part)
    return val


def _set(record: Dict[str, Any], field: str, value: Any) -> None:
    """Set *field* (dot-notation) on *record* in-place."""
    parts = field.split(".")
    d = record
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def cap_field(
    record: Dict[str, Any],
    field: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> Dict[str, Any]:
    """Return a copy of *record* with *field* clamped to [minimum, maximum].

    Non-numeric values and missing fields are left untouched.
    """
    import copy

    record = copy.copy(record)
    val = _get(record, field)
    if not isinstance(val, (int, float)):
        return record
    clamped = val
    if minimum is not None:
        clamped = max(clamped, minimum)
    if maximum is not None:
        clamped = min(clamped, maximum)
    if clamped != val:
        _set(record, field, clamped)
    return record


def cap_fields(
    record: Dict[str, Any],
    specs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply multiple cap specs to *record*.

    Each spec is a dict with keys: ``field``, optionally ``min`` and/or ``max``.
    """
    for spec in specs:
        record = cap_field(
            record,
            field=spec["field"],
            minimum=spec.get("min"),
            maximum=spec.get("max"),
        )
    return record


def apply_caps(
    records: Iterable[Dict[str, Any]],
    specs: List[Dict[str, Any]],
) -> Iterator[Dict[str, Any]]:
    """Yield records with all cap *specs* applied."""
    for record in records:
        yield cap_fields(record, specs)
