"""Alert rules: evaluate records against threshold conditions."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

Record = Dict[str, Any]


def _get(record: Record, field: str) -> Optional[Any]:
    """Return nested field value using dot notation."""
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _coerce(value: Any) -> float:
    """Coerce a value to float; raise ValueError if not possible."""
    return float(value)


def check_threshold(
    record: Record,
    field: str,
    op: str,
    threshold: float,
) -> bool:
    """Return True if record[field] <op> threshold.

    Supported ops: gt, gte, lt, lte, eq, ne.
    Returns False when field is absent or not numeric.
    """
    value = _get(record, field)
    if value is None:
        return False
    try:
        numeric = _coerce(value)
    except (TypeError, ValueError):
        return False
    ops = {
        "gt": numeric > threshold,
        "gte": numeric >= threshold,
        "lt": numeric < threshold,
        "lte": numeric <= threshold,
        "eq": numeric == threshold,
        "ne": numeric != threshold,
    }
    if op not in ops:
        raise ValueError(f"Unknown operator: {op!r}. Choose from {list(ops)}")
    return ops[op]


def alert_records(
    records: Iterable[Record],
    rules: List[Tuple[str, str, float]],
    match_all: bool = True,
) -> Iterator[Record]:
    """Yield records that satisfy alert rules.

    Each rule is (field, op, threshold).
    If match_all=True all rules must match; otherwise any rule suffices.
    """
    for record in records:
        results = [check_threshold(record, f, op, t) for f, op, t in rules]
        if not results:
            continue
        if match_all and all(results):
            yield record
        elif not match_all and any(results):
            yield record


def annotate_alerts(
    records: Iterable[Record],
    rules: List[Tuple[str, str, float]],
    label: str = "_alert",
) -> Iterator[Record]:
    """Pass every record through, adding label=True when any rule fires."""
    for record in records:
        fired = any(check_threshold(record, f, op, t) for f, op, t in rules)
        yield {**record, label: fired}
