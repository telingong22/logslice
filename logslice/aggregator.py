"""Simple aggregation utilities for grouped log analysis."""
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


def count_by(records: Iterable[Dict[str, Any]], field: str) -> Counter:
    """Count log records grouped by the value of *field*."""
    counter: Counter = Counter()
    for record in records:
        value = record.get(field)
        if value is not None:
            counter[str(value)] += 1
    return counter


def group_by(records: Iterable[Dict[str, Any]], field: str) -> Dict[str, List[Dict[str, Any]]]:
    """Group records into lists keyed by the value of *field*."""
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        value = record.get(field)
        if value is not None:
            groups[str(value)].append(record)
    return dict(groups)


def summarise(records: Iterable[Dict[str, Any]], field: str) -> Dict[str, Any]:
    """Return basic numeric summary statistics for a numeric *field*."""
    values: List[float] = []
    for record in records:
        raw = record.get(field)
        if raw is not None:
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                pass

    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "sum": None}

    total = sum(values)
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": total / len(values),
        "sum": total,
    }


def top_n(counter: Counter, n: int = 10) -> List[tuple]:
    """Return the *n* most common entries from a Counter."""
    return counter.most_common(n)


def filter_by(records: Iterable[Dict[str, Any]], field: str, value: Any) -> List[Dict[str, Any]]:
    """Return records where *field* matches *value*.

    Comparison is performed after converting both the record value and the
    target *value* to strings, so callers do not need to worry about type
    mismatches between numeric log fields and string query values.
    """
    target = str(value)
    return [record for record in records if str(record.get(field, "")) == target]
