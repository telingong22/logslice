"""Compute percentile statistics over a numeric field across log records."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Iterator, List, Optional


def _get(record: Dict[str, Any], field: str) -> Optional[float]:
    """Return the float value of *field* in *record*, or None if missing/non-numeric."""
    val = record.get(field)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def compute_percentiles(
    records: Iterable[Dict[str, Any]],
    field: str,
    percentiles: List[float],
) -> Dict[str, float]:
    """Collect all numeric values for *field* and return requested percentiles.

    *percentiles* should be values in the range [0, 100].
    Returns a dict mapping "pN" -> value (e.g. {"p50": 1.2, "p99": 9.8}).
    Raises ValueError if no valid values are found or a percentile is out of range.
    """
    for p in percentiles:
        if not (0.0 <= p <= 100.0):
            raise ValueError(f"Percentile must be between 0 and 100, got {p}")

    values: List[float] = []
    for record in records:
        v = _get(record, field)
        if v is not None:
            values.append(v)

    if not values:
        raise ValueError(f"No numeric values found for field '{field}'")

    values.sort()
    n = len(values)
    result: Dict[str, float] = {}

    for p in percentiles:
        if p == 0.0:
            result[f"p{int(p)}"] = values[0]
        elif p == 100.0:
            result[f"p{int(p)}"] = values[-1]
        else:
            rank = (p / 100.0) * (n - 1)
            lower = math.floor(rank)
            upper = math.ceil(rank)
            frac = rank - lower
            interpolated = values[lower] * (1.0 - frac) + values[upper] * frac
            label = f"p{int(p)}" if p == int(p) else f"p{p}"
            result[label] = round(interpolated, 6)

    return result


def percentile_records(
    records: Iterable[Dict[str, Any]],
    field: str,
    percentiles: List[float],
) -> Iterator[Dict[str, Any]]:
    """Yield a single summary record containing percentile stats for *field*."""
    stats = compute_percentiles(records, field, percentiles)
    record: Dict[str, Any] = {"field": field, "count": None}
    record.update(stats)
    yield record
