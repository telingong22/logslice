"""Field validation for log records."""
from typing import Any, Dict, Iterable, Iterator, List, Optional


def validate_required(record: Dict, fields: List[str]) -> List[str]:
    """Return list of required fields missing from record."""
    return [f for f in fields if f not in record]


def validate_type(record: Dict, field: str, expected_type: type) -> bool:
    """Return True if field exists and matches expected_type."""
    if field not in record:
        return False
    return isinstance(record[field], expected_type)


def validate_allowed_values(record: Dict, field: str, allowed: List[Any]) -> bool:
    """Return True if field value is in allowed list."""
    if field not in record:
        return False
    return record[field] in allowed


def validate_record(
    record: Dict,
    required: Optional[List[str]] = None,
    types: Optional[Dict[str, type]] = None,
    allowed: Optional[Dict[str, List[Any]]] = None,
) -> List[str]:
    """Run all validations and return list of error messages."""
    errors: List[str] = []
    if required:
        missing = validate_required(record, required)
        for f in missing:
            errors.append(f"missing required field: {f!r}")
    if types:
        for field, expected in types.items():
            if field in record and not isinstance(record[field], expected):
                actual = type(record[field]).__name__
                errors.append(
                    f"field {field!r} expected {expected.__name__}, got {actual}"
                )
    if allowed:
        for field, values in allowed.items():
            if field in record and record[field] not in values:
                errors.append(
                    f"field {field!r} value {record[field]!r} not in allowed {values}"
                )
    return errors


def filter_valid(
    records: Iterable[Dict],
    required: Optional[List[str]] = None,
    types: Optional[Dict[str, type]] = None,
    allowed: Optional[Dict[str, List[Any]]] = None,
) -> Iterator[Dict]:
    """Yield only records that pass all validations."""
    for record in records:
        errors = validate_record(record, required=required, types=types, allowed=allowed)
        if not errors:
            yield record
