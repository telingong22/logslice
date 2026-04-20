"""Rate calculation: compute events-per-interval from a stream of records."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Iterator

from logslice.filters import extract_timestamp


def _bucket(ts: float, interval_seconds: float) -> float:
    """Return the start of the bucket that *ts* falls into."""
    return float(int(ts // interval_seconds) * interval_seconds)


def compute_rate(
    records: Iterable[dict],
    interval_seconds: float = 60.0,
    ts_field: str = "timestamp",
) -> list[dict]:
    """Count records per time bucket and return rate records.

    Each output record has:
      - ``bucket``  : ISO-ish label for the window start (float epoch seconds)
      - ``count``   : number of log lines in that window
      - ``rate_per_sec``: count / interval_seconds
    """
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    counts: dict[float, int] = defaultdict(int)

    for record in records:
        ts = extract_timestamp(record, ts_field)
        if ts is None:
            continue
        b = _bucket(ts, interval_seconds)
        counts[b] += 1

    result = []
    for bucket_start in sorted(counts):
        count = counts[bucket_start]
        result.append(
            {
                "bucket": bucket_start,
                "count": count,
                "rate_per_sec": round(count / interval_seconds, 6),
            }
        )
    return result


def rate_records(records: Iterable[dict], **kwargs) -> Iterator[dict]:
    """Yield rate records; thin wrapper so callers can use iterator style."""
    yield from compute_rate(records, **kwargs)
