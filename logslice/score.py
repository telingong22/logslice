"""Scoring: assign a numeric relevance score to each log record."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


def _get(record: Dict[str, Any], field: str) -> Any:
    """Return a (possibly nested) field value using dot notation."""
    parts = field.split(".")
    cur: Any = record
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def score_field_match(
    records: Iterable[Dict[str, Any]],
    rules: List[Tuple[str, Any, float]],
    score_field: str = "_score",
    base: float = 0.0,
) -> Iterator[Dict[str, Any]]:
    """Yield records annotated with a cumulative score.

    Each rule is a (field, value, weight) triple.  If the record's field
    equals *value* the *weight* is added to the running score.  *value*
    may also be a callable predicate ``(v) -> bool``.
    """
    for record in records:
        total = base
        for field, value, weight in rules:
            actual = _get(record, field)
            if callable(value):
                if value(actual):
                    total += weight
            else:
                if actual == value:
                    total += weight
        out = dict(record)
        out[score_field] = round(total, 6)
        yield out


def threshold_filter(
    records: Iterable[Dict[str, Any]],
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    score_field: str = "_score",
) -> Iterator[Dict[str, Any]]:
    """Yield only records whose score satisfies the given bounds."""
    for record in records:
        score = record.get(score_field, 0.0)
        if min_score is not None and score < min_score:
            continue
        if max_score is not None and score > max_score:
            continue
        yield record


def top_scoring(
    records: Iterable[Dict[str, Any]],
    n: int,
    score_field: str = "_score",
) -> List[Dict[str, Any]]:
    """Return the *n* highest-scoring records (descending order)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    ranked = sorted(records, key=lambda r: r.get(score_field, 0.0), reverse=True)
    return ranked[:n]
