"""High-level pipeline that wires parser, filters, transforms, and output."""

from typing import Any, Dict, Iterable, Iterator, List, Optional

from logslice.filters import extract_timestamp, in_time_range, match_pattern
from logslice.parser import parse_line
from logslice.transform import apply_transforms


def _iter_records(lines: Iterable[str]) -> Iterator[Dict[str, Any]]:
    """Parse lines, skipping those that cannot be decoded."""
    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        record = parse_line(line)
        if record is not None:
            yield record


def run_pipeline(
    lines: Iterable[str],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    patterns: Optional[List[str]] = None,
    renames: Optional[Dict[str, str]] = None,
    drop: Optional[List[str]] = None,
    keep: Optional[List[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """Full processing pipeline: parse → filter → transform.

    Yields processed records that pass all filters.
    """
    records = _iter_records(lines)

    for record in records:
        # Time range filter
        if start or end:
            ts = extract_timestamp(record)
            if not in_time_range(ts, start, end):
                continue

        # Field pattern filters (all must match)
        if patterns:
            if not all(match_pattern(record, p) for p in patterns):
                continue

        yield record

    # transforms applied lazily after filtering via generator chain would
    # require restructuring; we do it as a second pass for clarity.


def run_pipeline_transformed(
    lines: Iterable[str],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    patterns: Optional[List[str]] = None,
    renames: Optional[Dict[str, str]] = None,
    drop: Optional[List[str]] = None,
    keep: Optional[List[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """Pipeline with transform stage applied after filtering."""
    filtered = run_pipeline(
        lines,
        start=start,
        end=end,
        patterns=patterns,
    )
    return apply_transforms(filtered, renames=renames, drop=drop, keep=keep)
