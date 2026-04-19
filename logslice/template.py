"""Template-based formatting for log records."""
from __future__ import annotations
import re
from typing import Any, Dict, Iterable, Iterator

_PLACEHOLDER = re.compile(r"\{([^}]+)\}")


def _get(record: Dict[str, Any], key: str, default: str = "") -> str:
    """Retrieve a possibly nested key using dot notation."""
    parts = key.split(".")
    val: Any = record
    for part in parts:
        if not isinstance(val, dict):
            return default
        val = val.get(part)
        if val is None:
            return default
    return str(val)


def render_template(template: str, record: Dict[str, Any], default: str = "") -> str:
    """Render *template* by substituting {field} placeholders from *record*.

    Nested fields can be accessed with dot notation: {request.method}.
    Missing fields are replaced with *default*.
    """
    def replacer(m: re.Match) -> str:  # type: ignore[type-arg]
        return _get(record, m.group(1), default)

    return _PLACEHOLDER.sub(replacer, template)


def apply_template(
    records: Iterable[Dict[str, Any]],
    template: str,
    output_field: str = "_rendered",
    default: str = "",
) -> Iterator[Dict[str, Any]]:
    """Yield records with an additional *output_field* containing the rendered template."""
    for record in records:
        rendered = render_template(template, record, default=default)
        yield {**record, output_field: rendered}


def format_as_template(
    records: Iterable[Dict[str, Any]],
    template: str,
    default: str = "",
) -> Iterator[str]:
    """Yield rendered strings for each record — useful for plain-text output."""
    for record in records:
        yield render_template(template, record, default=default)
