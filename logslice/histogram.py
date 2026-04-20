"""Build text histograms from log field values or time-bucketed counts."""
from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple


def field_histogram(
    records: Iterable[dict],
    field: str,
    top: int = 10,
) -> List[Tuple[str, int]]:
    """Count occurrences of *field* values and return top-N sorted by count desc."""
    counts: Counter = Counter()
    for rec in records:
        val = rec.get(field)
        if val is not None:
            counts[str(val)] += 1
    return counts.most_common(top)


def render_bar(
    label: str,
    count: int,
    max_count: int,
    width: int = 40,
    fill: str = "█",
) -> str:
    """Render a single histogram bar as a string."""
    bar_len = int(width * count / max_count) if max_count else 0
    bar = fill * bar_len
    return f"{label:<20s} | {bar:<{width}s} {count}"


def render_histogram(
    data: List[Tuple[str, int]],
    width: int = 40,
    fill: str = "█",
    title: Optional[str] = None,
) -> str:
    """Return a multi-line ASCII histogram string from (label, count) pairs."""
    if not data:
        return "(no data)"
    lines: List[str] = []
    if title:
        lines.append(title)
        lines.append("-" * (20 + 3 + width + 10))
    max_count = max(c for _, c in data)
    for label, count in data:
        lines.append(render_bar(label, count, max_count, width=width, fill=fill))
    return "\n".join(lines)


def histogram_records(
    records: Iterable[dict],
    field: str,
    top: int = 10,
    width: int = 40,
    title: Optional[str] = None,
) -> str:
    """Convenience: compute field histogram and render it in one call."""
    data = field_histogram(records, field, top=top)
    return render_histogram(data, width=width, title=title or f"Histogram: {field}")
