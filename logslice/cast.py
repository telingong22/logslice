"""Field type casting: convert field values to int, float, bool, or str."""

from typing import Any, Dict, Iterable, Iterator, List, Optional

_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}


def _cast_value(value: Any, target_type: str) -> Any:
    """Cast *value* to *target_type*. Raises ValueError on failure."""
    if target_type == "int":
        return int(float(value))
    if target_type == "float":
        return float(value)
    if target_type == "bool":
        s = str(value).strip().lower()
        if s in _BOOL_TRUE:
            return True
        if s in _BOOL_FALSE:
            return False
        raise ValueError(f"Cannot cast {value!r} to bool")
    if target_type == "str":
        return str(value)
    raise ValueError(f"Unknown target type: {target_type!r}")


def cast_field(
    record: Dict[str, Any],
    field: str,
    target_type: str,
    default: Optional[Any] = None,
) -> Dict[str, Any]:
    """Return a copy of *record* with *field* cast to *target_type*.

    If the field is missing or the cast fails, *default* is used.  When
    *default* is ``None`` and the cast fails the field is left unchanged.
    """
    record = dict(record)
    if field not in record:
        return record
    try:
        record[field] = _cast_value(record[field], target_type)
    except (ValueError, TypeError):
        if default is not None:
            record[field] = default
    return record


def cast_fields(
    record: Dict[str, Any],
    specs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply multiple cast specs to *record*.

    Each spec is a dict with keys ``field``, ``type``, and optionally
    ``default``.
    """
    for spec in specs:
        record = cast_field(
            record,
            spec["field"],
            spec["type"],
            spec.get("default"),
        )
    return record


def apply_casts(
    records: Iterable[Dict[str, Any]],
    specs: List[Dict[str, Any]],
) -> Iterator[Dict[str, Any]]:
    """Yield records with all cast *specs* applied."""
    for record in records:
        yield cast_fields(record, specs)
