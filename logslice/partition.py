"""Partition log records into named buckets based on field values or rules."""

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple


def _get(record: dict, field: str, default: Any = None) -> Any:
    """Retrieve a possibly nested field using dot notation."""
    parts = field.split(".")
    val = record
    for part in parts:
        if not isinstance(val, dict):
            return default
        val = val.get(part, default)
    return val


def partition_by_value(
    records: Iterable[dict],
    field: str,
    default_bucket: str = "__other__",
) -> Dict[str, List[dict]]:
    """Split records into buckets keyed by the value of *field*."""
    buckets: Dict[str, List[dict]] = {}
    for record in records:
        key = _get(record, field)
        bucket = str(key) if key is not None else default_bucket
        buckets.setdefault(bucket, []).append(record)
    return buckets


def partition_by_rules(
    records: Iterable[dict],
    rules: List[Tuple[str, Callable[[dict], bool]]],
    default_bucket: str = "__other__",
) -> Dict[str, List[dict]]:
    """Split records using ordered (name, predicate) rules; first match wins."""
    buckets: Dict[str, List[dict]] = {}
    for record in records:
        matched = False
        for name, predicate in rules:
            try:
                if predicate(record):
                    buckets.setdefault(name, []).append(record)
                    matched = True
                    break
            except Exception:
                continue
        if not matched:
            buckets.setdefault(default_bucket, []).append(record)
    return buckets


def partition_records(
    records: Iterable[dict],
    field: Optional[str] = None,
    rules: Optional[List[Tuple[str, Callable[[dict], bool]]]] = None,
    default_bucket: str = "__other__",
) -> Dict[str, List[dict]]:
    """Unified entry point: use rules if provided, otherwise partition by field value."""
    if rules is not None:
        return partition_by_rules(records, rules, default_bucket=default_bucket)
    if field is not None:
        return partition_by_value(records, field, default_bucket=default_bucket)
    raise ValueError("Either 'field' or 'rules' must be provided.")


def iter_partitions(
    buckets: Dict[str, List[dict]],
) -> Iterator[Tuple[str, List[dict]]]:
    """Yield (bucket_name, records) pairs sorted by bucket name."""
    for name in sorted(buckets):
        yield name, buckets[name]
