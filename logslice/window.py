"""Sliding and tumbling window aggregations over log records."""

from typing import Iterable, Iterator, List, Dict, Any, Optional
from datetime import datetime, timedelta
from logslice.filters import extract_timestamp


def tumbling_windows(
    records: Iterable[Dict[str, Any]],
    interval_seconds: float,
    ts_field: str = "timestamp",
) -> Iterator[List[Dict[str, Any]]]:
    """Yield non-overlapping windows of fixed duration."""
    window: List[Dict[str, Any]] = []
    window_start: Optional[float] = None

    for record in records:
        ts = extract_timestamp(record, ts_field)
        if ts is None:
            continue
        t = ts.timestamp()
        if window_start is None:
            window_start = t
        if t - window_start >= interval_seconds:
            if window:
                yield window
            window = [record]
            window_start = t
        else:
            window.append(record)

    if window:
        yield window


def sliding_windows(
    records: Iterable[Dict[str, Any]],
    window_seconds: float,
    step_seconds: float,
    ts_field: str = "timestamp",
) -> Iterator[List[Dict[str, Any]]]:
    """Yield overlapping windows advancing by step_seconds."""
    buffered: List[tuple] = []
    next_emit: Optional[float] = None

    for record in records:
        ts = extract_timestamp(record, ts_field)
        if ts is None:
            continue
        t = ts.timestamp()
        if next_emit is None:
            next_emit = t + step_seconds
        buffered.append((t, record))
        while t >= next_emit:
            cutoff = next_emit - window_seconds
            buffered = [(bt, br) for bt, br in buffered if bt >= cutoff]
            yield [br for _, br in buffered if bt <= next_emit for bt, br in [(bt, br)]]
            next_emit += step_seconds


def window_summary(
    window: List[Dict[str, Any]],
    count_field: Optional[str] = None,
) -> Dict[str, Any]:
    """Return basic stats for a window."""
    summary: Dict[str, Any] = {"count": len(window)}
    if count_field and window:
        values = []
        for r in window:
            v = r.get(count_field)
            try:
                values.append(float(v))
            except (TypeError, ValueError):
                pass
        if values:
            summary["sum"] = sum(values)
            summary["min"] = min(values)
            summary["max"] = max(values)
            summary["avg"] = sum(values) / len(values)
    return summary
