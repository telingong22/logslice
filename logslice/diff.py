"""Diff consecutive or paired log records by field changes."""
from typing import Iterable, Iterator, List, Optional, Set


def diff_consecutive(
    records: Iterable[dict],
    fields: Optional[List[str]] = None,
    tag_field: str = "_diff",
) -> Iterator[dict]:
    """Yield records annotated with fields that changed since the previous record."""
    prev: Optional[dict] = None
    for record in records:
        out = dict(record)
        if prev is None:
            out[tag_field] = []
        else:
            keys = fields if fields is not None else list(record.keys() | prev.keys())
            changed = [k for k in keys if record.get(k) != prev.get(k)]
            out[tag_field] = changed
        prev = record
        yield out


def diff_pair(a: dict, b: dict, fields: Optional[List[str]] = None) -> dict:
    """Return a dict of {field: (old, new)} for fields that differ between a and b."""
    keys = fields if fields is not None else list(set(a.keys()) | set(b.keys()))
    return {k: (a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)}


def changed_only(
    records: Iterable[dict],
    fields: Optional[List[str]] = None,
    tag_field: str = "_diff",
) -> Iterator[dict]:
    """Like diff_consecutive but skips records with no changes (after the first)."""
    first = True
    for record in diff_consecutive(records, fields=fields, tag_field=tag_field):
        if first or record.get(tag_field):
            yield record
            first = False
