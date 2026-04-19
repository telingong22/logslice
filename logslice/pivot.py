"""Pivot log records: group by a key field and collect values of a value field."""
from collections import defaultdict
from typing import Iterable, Iterator, Dict, Any, List, Optional


def pivot_collect(
    records: Iterable[Dict[str, Any]],
    key_field: str,
    value_field: str,
) -> Dict[str, List[Any]]:
    """Group records by key_field, collecting all value_field values."""
    result: Dict[str, List[Any]] = defaultdict(list)
    for record in records:
        k = record.get(key_field)
        v = record.get(value_field)
        if k is not None and v is not None:
            result[str(k)].append(v)
    return dict(result)


def pivot_count(
    records: Iterable[Dict[str, Any]],
    key_field: str,
    value_field: str,
) -> Dict[str, int]:
    """Group records by key_field, counting occurrences of value_field."""
    collected = pivot_collect(records, key_field, value_field)
    return {k: len(v) for k, v in collected.items()}


def pivot_to_records(
    collected: Dict[str, List[Any]],
    key_field: str,
    value_field: str,
    aggregate: str = "list",
) -> Iterator[Dict[str, Any]]:
    """Convert pivot result back to records with optional aggregation.

    aggregate: 'list' | 'count' | 'first' | 'last'
    """
    for key, values in collected.items():
        if aggregate == "count":
            agg_value: Any = len(values)
        elif aggregate == "first":
            agg_value = values[0] if values else None
        elif aggregate == "last":
            agg_value = values[-1] if values else None
        else:
            agg_value = values
        yield {key_field: key, value_field: agg_value}


def pivot_records(
    records: Iterable[Dict[str, Any]],
    key_field: str,
    value_field: str,
    aggregate: str = "list",
) -> Iterator[Dict[str, Any]]:
    """End-to-end pivot: collect then emit aggregated records."""
    collected = pivot_collect(records, key_field, value_field)
    return pivot_to_records(collected, key_field, value_field, aggregate)
