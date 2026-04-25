"""Rollup: aggregate numeric fields over a stream of records."""

from typing import Any, Dict, Iterable, Iterator, List, Optional


def _get(record: Dict[str, Any], field: str) -> Optional[float]:
    """Return a float value for *field* in *record*, or None if missing/non-numeric."""
    val = record.get(field)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def rollup_sum(
    records: Iterable[Dict[str, Any]],
    fields: List[str],
) -> Dict[str, float]:
    """Return the sum of each field across all records."""
    totals: Dict[str, float] = {f: 0.0 for f in fields}
    for record in records:
        for field in fields:
            v = _get(record, field)
            if v is not None:
                totals[field] += v
    return totals


def rollup_avg(
    records: Iterable[Dict[str, Any]],
    fields: List[str],
) -> Dict[str, Optional[float]]:
    """Return the mean of each field across all records."""
    totals: Dict[str, float] = {f: 0.0 for f in fields}
    counts: Dict[str, int] = {f: 0 for f in fields}
    for record in records:
        for field in fields:
            v = _get(record, field)
            if v is not None:
                totals[field] += v
                counts[field] += 1
    return {
        f: (totals[f] / counts[f] if counts[f] > 0 else None)
        for f in fields
    }


def rollup_min_max(
    records: Iterable[Dict[str, Any]],
    fields: List[str],
) -> Dict[str, Dict[str, Optional[float]]]:
    """Return {field: {min: ..., max: ...}} for each field."""
    mins: Dict[str, Optional[float]] = {f: None for f in fields}
    maxs: Dict[str, Optional[float]] = {f: None for f in fields}
    for record in records:
        for field in fields:
            v = _get(record, field)
            if v is None:
                continue
            if mins[field] is None or v < mins[field]:  # type: ignore[operator]
                mins[field] = v
            if maxs[field] is None or v > maxs[field]:  # type: ignore[operator]
                maxs[field] = v
    return {f: {"min": mins[f], "max": maxs[f]} for f in fields}


def rollup_records(
    records: Iterable[Dict[str, Any]],
    fields: List[str],
    ops: List[str],
) -> Iterator[Dict[str, Any]]:
    """Yield a single summary record containing requested rollup ops.

    *ops* may contain any combination of: 'sum', 'avg', 'min', 'max'.
    """
    all_records = list(records)
    result: Dict[str, Any] = {}

    if "sum" in ops:
        for field, val in rollup_sum(all_records, fields).items():
            result[f"{field}_sum"] = val

    if "avg" in ops:
        for field, val in rollup_avg(all_records, fields).items():
            result[f"{field}_avg"] = val

    if "min" in ops or "max" in ops:
        mm = rollup_min_max(all_records, fields)
        for field, bounds in mm.items():
            if "min" in ops:
                result[f"{field}_min"] = bounds["min"]
            if "max" in ops:
                result[f"{field}_max"] = bounds["max"]

    result["_count"] = len(all_records)
    yield result
