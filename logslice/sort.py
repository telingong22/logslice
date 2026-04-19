"""Sorting utilities for log records."""
from typing import Iterable, Iterator, Optional


def sort_records(
    records: Iterable[dict],
    field: str,
    reverse: bool = False,
    missing_last: bool = True,
) -> Iterator[dict]:
    """Sort records by a given field value.

    Args:
        records: Iterable of parsed log record dicts.
        field: Top-level field name to sort by.
        reverse: If True, sort descending.
        missing_last: If True, records missing the field sort after others.

    Yields:
        Records in sorted order.
    """
    sentinel = object()

    def _key(record: dict):
        val = record.get(field, sentinel)
        if val is sentinel:
            # missing values go last (or first if reverse)
            return (1, "") if missing_last else (0, "")
        return (0, val) if not reverse else (0, val)

    collected = list(records)

    def sort_key(record: dict):
        val = record.get(field, sentinel)
        missing = val is sentinel
        if missing_last:
            return (1 if missing else 0, "" if missing else val)
        else:
            return (0 if missing else 1, "" if missing else val)

    yield from sorted(collected, key=sort_key, reverse=reverse)


def sort_by_timestamp(
    records: Iterable[dict],
    field: str = "timestamp",
    reverse: bool = False,
) -> Iterator[dict]:
    """Convenience wrapper: sort records by a timestamp field."""
    yield from sort_records(records, field=field, reverse=reverse)
