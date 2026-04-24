"""Resample time-series log records into fixed-size time buckets."""

from datetime import datetime, timezone
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.filters import extract_timestamp


def _floor_to_bucket(ts: datetime, interval_seconds: int) -> datetime:
    """Floor a datetime to the nearest bucket boundary."""
    epoch = ts.timestamp()
    floored = (epoch // interval_seconds) * interval_seconds
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def resample_records(
    records: Iterable[Dict],
    interval_seconds: int,
    ts_field: str = "timestamp",
    agg: str = "count",
    value_field: Optional[str] = None,
) -> Iterator[Dict]:
    """Bucket records by time interval and emit one summary record per bucket.

    Args:
        records: Input log records.
        interval_seconds: Width of each bucket in seconds.
        ts_field: Field name used to extract the timestamp.
        agg: Aggregation to apply — 'count', 'sum', 'avg', 'min', or 'max'.
        value_field: Numeric field to aggregate (required for sum/avg/min/max).

    Yields:
        One dict per non-empty bucket with keys: bucket, count, and the
        aggregated value (named after *agg*) when value_field is given.
    """
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if agg not in {"count", "sum", "avg", "min", "max"}:
        raise ValueError(f"Unknown aggregation: {agg!r}")
    if agg != "count" and value_field is None:
        raise ValueError(f"value_field is required for aggregation {agg!r}")

    buckets: Dict[datetime, List] = {}

    for record in records:
        ts = extract_timestamp(record, ts_field)
        if ts is None:
            continue
        bucket = _floor_to_bucket(ts, interval_seconds)
        buckets.setdefault(bucket, [])
        if value_field is not None:
            raw = record.get(value_field)
            try:
                buckets[bucket].append(float(raw))
            except (TypeError, ValueError):
                pass
        else:
            buckets[bucket].append(None)

    for bucket in sorted(buckets):
        values = buckets[bucket]
        result: Dict = {
            "bucket": bucket.isoformat(),
            "count": len(values),
        }
        if value_field is not None:
            nums = [v for v in values if v is not None]
            if nums:
                if agg == "sum":
                    result[agg] = sum(nums)
                elif agg == "avg":
                    result[agg] = sum(nums) / len(nums)
                elif agg == "min":
                    result[agg] = min(nums)
                elif agg == "max":
                    result[agg] = max(nums)
            else:
                result[agg] = None
        yield result
