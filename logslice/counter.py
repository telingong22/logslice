"""Line and field counters for log streams."""
from typing import Iterable, Iterator, Dict, Any, Optional
from collections import Counter


def count_lines(records: Iterable[Dict[str, Any]]) -> int:
    """Return total number of records."""
    return sum(1 for _ in records)


def count_field_values(
    records: Iterable[Dict[str, Any]],
    field: str,
) -> Counter:
    """Count occurrences of each value for *field*."""
    c: Counter = Counter()
    for rec in records:
        if field in rec:
            c[rec[field]] += 1
    return c


def count_per_interval(
    records: Iterable[Dict[str, Any]],
    ts_field: str = "time",
    interval: int = 60,
) -> Dict[int, int]:
    """Bucket records into *interval*-second buckets by *ts_field* (unix epoch).

    Records whose timestamp cannot be converted to float are skipped.
    Returns a dict mapping bucket_start -> count.
    """
    buckets: Dict[int, int] = {}
    for rec in records:
        raw = rec.get(ts_field)
        if raw is None:
            continue
        try:
            ts = float(raw)
        except (TypeError, ValueError):
            continue
        bucket = int(ts // interval) * interval
        buckets[bucket] = buckets.get(bucket, 0) + 1
    return buckets


def annotate_index(
    records: Iterable[Dict[str, Any]],
    field: str = "_index",
    start: int = 0,
) -> Iterator[Dict[str, Any]]:
    """Yield records with a sequential integer *field* added."""
    for i, rec in enumerate(records, start=start):
        yield {**rec, field: i}
