"""Baseline comparison: compare a stream of records against a stored baseline snapshot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

Record = Dict[str, object]


def load_baseline(path: str) -> List[Record]:
    """Load a baseline snapshot from a JSON-lines file."""
    records: List[Record] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_baseline(records: Iterable[Record], path: str) -> int:
    """Persist *records* as a JSON-lines baseline file.  Returns number of records written."""
    count = 0
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
            count += 1
    return count


def diff_against_baseline(
    records: Iterable[Record],
    baseline: List[Record],
    key_field: str,
) -> Iterator[Record]:
    """Yield records that are *new* or *changed* compared to *baseline*.

    A record is identified by *key_field*.  If the key is absent in a record it
    is always emitted (treated as new).  Each emitted record is annotated with
    ``_baseline_status`` set to ``"new"`` or ``"changed"``.
    """
    index: Dict[str, Record] = {}
    for b in baseline:
        k = b.get(key_field)
        if k is not None:
            index[str(k)] = b

    for rec in records:
        k = rec.get(key_field)
        if k is None:
            yield {**rec, "_baseline_status": "new"}
            continue
        key_str = str(k)
        if key_str not in index:
            yield {**rec, "_baseline_status": "new"}
        elif rec != index[key_str]:
            yield {**rec, "_baseline_status": "changed"}


def missing_from_stream(
    records: Iterable[Record],
    baseline: List[Record],
    key_field: str,
) -> List[Record]:
    """Return baseline records whose key is absent from *records*.

    Useful for detecting records that disappeared between runs.
    """
    seen: set = set()
    for rec in records:
        k = rec.get(key_field)
        if k is not None:
            seen.add(str(k))

    missing: List[Record] = []
    for b in baseline:
        k = b.get(key_field)
        if k is not None and str(k) not in seen:
            missing.append({**b, "_baseline_status": "missing"})
    return missing
