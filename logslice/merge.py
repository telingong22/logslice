"""Merge and interleave multiple sorted log streams by timestamp."""
from typing import Iterable, Iterator, List, Optional
import heapq

from logslice.filters import extract_timestamp


def merge_streams(
    streams: List[Iterable[dict]],
    timestamp_field: str = "timestamp",
    missing_last: bool = True,
) -> Iterator[dict]:
    """Merge multiple record iterables, yielding records in timestamp order."""
    SENTINEL = "9999-99-99" if missing_last else ""

    def _keyed(stream):
        for record in stream:
            ts = extract_timestamp(record, timestamp_field) or SENTINEL
            yield (ts, record)

    iterators = [_keyed(s) for s in streams]
    for _ts, record in heapq.merge(*iterators, key=lambda x: x[0]):
        yield record


def merge_files(
    file_paths: List[str],
    timestamp_field: str = "timestamp",
    missing_last: bool = True,
) -> Iterator[dict]:
    """Open and merge log files by timestamp."""
    import json
    from logslice.parser import parse_line

    def _read(path):
        with open(path) as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line:
                    record = parse_line(line)
                    if record is not None:
                        yield record

    streams = [_read(p) for p in file_paths]
    return merge_streams(streams, timestamp_field=timestamp_field, missing_last=missing_last)


def tag_source(
    records: Iterable[dict],
    source: str,
    field: str = "_source",
) -> Iterator[dict]:
    """Tag each record with a source label."""
    for record in records:
        tagged = dict(record)
        tagged[field] = source
        yield tagged
