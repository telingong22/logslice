"""Field pattern and time range filtering for parsed log entries."""

import re
from datetime import datetime, timezone
from typing import Any, Optional

# Common timestamp field names to probe when looking for a log entry's time
TIMESTAMP_FIELDS = ("timestamp", "time", "ts", "@timestamp", "date")


def extract_timestamp(entry: dict[str, Any]) -> Optional[datetime]:
    """Try to extract a datetime from a parsed log entry.

    Probes common timestamp field names and attempts to parse ISO-8601 strings
    as well as numeric Unix epoch values (int or float).

    Returns a timezone-aware datetime in UTC, or None if no timestamp found.
    """
    for field in TIMESTAMP_FIELDS:
        value = entry.get(field)
        if value is None:
            continue

        # Numeric epoch
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value, tz=timezone.utc)
            except (OSError, OverflowError, ValueError):
                continue

        # String — attempt ISO-8601 parsing
        if isinstance(value, str):
            # Python 3.11+ handles 'Z' natively; older versions need replacement
            normalized = value.strip().replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(normalized)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

    return None


def in_time_range(
    entry: dict[str, Any],
    start: Optional[datetime],
    end: Optional[datetime],
) -> bool:
    """Return True if the entry's timestamp falls within [start, end].

    If the entry has no parseable timestamp it is kept (returns True) so that
    non-timestamped lines are not silently dropped unless the caller explicitly
    wants to discard them.

    Either *start* or *end* may be None to indicate an open interval.
    """
    if start is None and end is None:
        return True

    ts = extract_timestamp(entry)
    if ts is None:
        return True

    if start is not None and ts < start:
        return False
    if end is not None and ts > end:
        return False
    return True


def match_pattern(entry: dict[str, Any], field: str, pattern: str) -> bool:
    """Return True if *entry[field]* matches the regex *pattern*.

    The match is performed against the string representation of the field
    value.  Missing fields never match.

    Args:
        entry:   Parsed log entry (dict).
        field:   Dot-notation field path, e.g. ``"level"`` or ``"http.method"``.
        pattern: Regular-expression string (case-sensitive).
    """
    value = _get_nested(entry, field)
    if value is None:
        return False
    try:
        return bool(re.search(pattern, str(value)))
    except re.error:
        # Treat an invalid regex as a literal substring match
        return pattern in str(value)


def _get_nested(entry: dict[str, Any], field: str) -> Any:
    """Resolve a dot-separated field path against a nested dict."""
    parts = field.split(".")
    node: Any = entry
    for part in parts:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node
