"""Correlate records across two streams by a shared key field."""

from typing import Any, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]


def _get(record: Record, field: str) -> Optional[Any]:
    """Return the value of *field* from *record*, or None if absent."""
    return record.get(field)


def build_index(records: Iterable[Record], key: str) -> Dict[Any, List[Record]]:
    """Index *records* by *key*, collecting all matching records per value."""
    index: Dict[Any, List[Record]] = {}
    for rec in records:
        val = _get(rec, key)
        if val is None:
            continue
        index.setdefault(val, []).append(rec)
    return index


def inner_join(
    left: Iterable[Record],
    right: Iterable[Record],
    key: str,
    prefix_left: str = "left_",
    prefix_right: str = "right_",
) -> Iterator[Record]:
    """Yield merged records where *key* exists in both streams."""
    index = build_index(right, key)
    for rec in left:
        val = _get(rec, key)
        if val is None:
            continue
        for match in index.get(val, []):
            merged: Record = {key: val}
            for k, v in rec.items():
                if k != key:
                    merged[prefix_left + k] = v
            for k, v in match.items():
                if k != key:
                    merged[prefix_right + k] = v
            yield merged


def left_join(
    left: Iterable[Record],
    right: Iterable[Record],
    key: str,
    prefix_left: str = "left_",
    prefix_right: str = "right_",
) -> Iterator[Record]:
    """Yield all left records, enriched with matching right records if found."""
    index = build_index(right, key)
    for rec in left:
        val = _get(rec, key)
        matches = index.get(val, [None]) if val is not None else [None]
        for match in matches:
            merged: Record = {key: val} if val is not None else {}
            for k, v in rec.items():
                if k != key:
                    merged[prefix_left + k] = v
            if match is not None:
                for k, v in match.items():
                    if k != key:
                        merged[prefix_right + k] = v
            yield merged


def correlate_records(
    left: Iterable[Record],
    right: Iterable[Record],
    key: str,
    mode: str = "inner",
    prefix_left: str = "left_",
    prefix_right: str = "right_",
) -> Iterator[Record]:
    """Correlate two record streams by *key*.

    *mode* is one of ``'inner'`` or ``'left'``.
    """
    if mode == "inner":
        return inner_join(left, right, key, prefix_left, prefix_right)
    if mode == "left":
        return left_join(left, right, key, prefix_left, prefix_right)
    raise ValueError(f"Unknown correlation mode: {mode!r}. Use 'inner' or 'left'.")
