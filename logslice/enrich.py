"""Field enrichment: derive new fields from existing ones."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional


def enrich_static(records: Iterable[Dict], field: str, value: Any) -> Iterator[Dict]:
    """Add a static constant value to every record."""
    for record in records:
        out = dict(record)
        out[field] = value
        yield out


def enrich_copy(records: Iterable[Dict], src: str, dst: str) -> Iterator[Dict]:
    """Copy the value of *src* into *dst* for each record."""
    for record in records:
        out = dict(record)
        if src in record:
            out[dst] = record[src]
        yield out


def enrich_regex(
    records: Iterable[Dict],
    src: str,
    pattern: str,
    mappings: Dict[str, str],
) -> Iterator[Dict]:
    """Extract named groups from *src* via *pattern* and write to *mappings*.

    *mappings* maps capture-group name -> destination field name.
    Records where *src* is absent or the pattern does not match are passed
    through unchanged.
    """
    compiled = re.compile(pattern)
    for record in records:
        out = dict(record)
        raw = record.get(src)
        if raw is not None:
            m = compiled.search(str(raw))
            if m:
                for group_name, dest_field in mappings.items():
                    val = m.groupdict().get(group_name)
                    if val is not None:
                        out[dest_field] = val
        yield out


def enrich_computed(
    records: Iterable[Dict],
    field: str,
    fn: Callable[[Dict], Any],
) -> Iterator[Dict]:
    """Derive *field* by applying *fn* to each record dict.

    If *fn* raises an exception the record is yielded without the new field.
    """
    for record in records:
        out = dict(record)
        try:
            out[field] = fn(record)
        except Exception:  # noqa: BLE001
            pass
        yield out


def apply_enrichments(
    records: Iterable[Dict],
    steps: List[Dict],
) -> Iterator[Dict]:
    """Apply a sequence of enrichment step descriptors.

    Each step is a dict with a ``type`` key and type-specific keys:
      - ``{"type": "static", "field": "env", "value": "prod"}``
      - ``{"type": "copy", "src": "host", "dst": "hostname"}``
      - ``{"type": "regex", "src": "msg", "pattern": r"(?P<code>\\d+)",
            "mappings": {"code": "status_code"}}``
    """
    stream: Iterable[Dict] = records
    for step in steps:
        t = step.get("type")
        if t == "static":
            stream = enrich_static(stream, step["field"], step["value"])
        elif t == "copy":
            stream = enrich_copy(stream, step["src"], step["dst"])
        elif t == "regex":
            stream = enrich_regex(
                stream, step["src"], step["pattern"], step.get("mappings", {})
            )
        else:
            raise ValueError(f"Unknown enrichment type: {t!r}")
    return stream
