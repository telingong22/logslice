"""Pipeline orchestration for logslice."""
from typing import Iterable, Iterator, IO
import sys

from logslice.parser import parse_line
from logslice.filters import extract_timestamp, in_time_range, match_pattern
from logslice.transform import apply_transforms
from logslice.dedup import dedup_records, dedup_consecutive


def _iter_records(lines: Iterable[str]) -> Iterator[dict]:
    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        record = parse_line(line)
        if record is not None:
            yield record


def run_pipeline(
    lines: Iterable[str],
    start: str | None = None,
    end: str | None = None,
    patterns: list[tuple[str, str]] | None = None,
    ts_field: str = "timestamp",
) -> Iterator[dict]:
    for record in _iter_records(lines):
        if start or end:
            ts = extract_timestamp(record, ts_field)
            if not in_time_range(ts, start, end):
                continue
        if patterns:
            if not all(match_pattern(record, field, pat) for field, pat in patterns):
                continue
        yield record


def run_pipeline_transformed(
    lines: Iterable[str],
    start: str | None = None,
    end: str | None = None,
    patterns: list[tuple[str, str]] | None = None,
    ts_field: str = "timestamp",
    transforms: dict | None = None,
    dedup_fields: list[str] | None = None,
    dedup_mode: str | None = None,
    dedup_consecutive_only: bool = False,
) -> Iterator[dict]:
    records = run_pipeline(lines, start=start, end=end, patterns=patterns, ts_field=ts_field)

    if transforms:
        from logslice.transform import apply_transforms
        records = (apply_transforms(r, transforms) for r in records)

    if dedup_consecutive_only:
        records = dedup_consecutive(records, fields=dedup_fields)
    elif dedup_mode:
        records = dedup_records(records, fields=dedup_fields, keep=dedup_mode)

    yield from records
