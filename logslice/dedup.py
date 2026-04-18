"""Deduplication utilities for log records."""
from typing import Iterable, Iterator, Any
import hashlib
import json


def _record_key(record: dict, fields: list[str] | None) -> str:
    """Return a hashable key for a record based on specified fields or full content."""
    if fields:
        subset = {f: record.get(f) for f in fields}
    else:
        subset = record
    serialised = json.dumps(subset, sort_keys=True, default=str)
    return hashlib.md5(serialised.encode()).hexdigest()


def dedup_records(
    records: Iterable[dict],
    fields: list[str] | None = None,
    keep: str = "first",
) -> Iterator[dict]:
    """Yield deduplicated records.

    Args:
        records: Iterable of parsed log records.
        fields: Fields to use as the dedup key. None means use all fields.
        keep: 'first' keeps the first occurrence; 'last' keeps the last.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    if keep == "first":
        seen: set[str] = set()
        for record in records:
            key = _record_key(record, fields)
            if key not in seen:
                seen.add(key)
                yield record
    else:  # last
        latest: dict[str, dict] = {}
        order: list[str] = []
        for record in records:
            key = _record_key(record, fields)
            if key not in latest:
                order.append(key)
            latest[key] = record
        for key in order:
            yield latest[key]


def dedup_consecutive(
    records: Iterable[dict],
    fields: list[str] | None = None,
) -> Iterator[dict]:
    """Yield records, dropping consecutive duplicates."""
    prev_key: str | None = None
    for record in records:
        key = _record_key(record, fields)
        if key != prev_key:
            yield record
            prev_key = key
