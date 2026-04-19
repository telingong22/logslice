"""Terminal colour highlighting for matched fields and patterns."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

ANSI = {
    "reset": "\033[0m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "bold": "\033[1m",
}


def _wrap(text: str, *codes: str) -> str:
    prefix = "".join(ANSI[c] for c in codes)
    return f"{prefix}{text}{ANSI['reset']}"


def highlight_keys(record: Dict[str, Any], keys: Iterable[str], colour: str = "cyan") -> str:
    """Return a formatted string with specified keys highlighted."""
    parts: List[str] = []
    for k, v in record.items():
        key_str = _wrap(k, colour) if k in set(keys) else k
        parts.append(f"{key_str}={v!r}")
    return " ".join(parts)


def highlight_pattern(
    text: str,
    pattern: str,
    colour: str = "yellow",
    ignore_case: bool = False,
) -> str:
    """Return *text* with all occurrences of *pattern* highlighted."""
    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error:
        return text

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        return _wrap(m.group(0), colour, "bold")

    return regex.sub(_replace, text)


def highlight_record(
    record: Dict[str, Any],
    keys: Optional[Iterable[str]] = None,
    pattern: Optional[str] = None,
    colour: str = "yellow",
) -> str:
    """Produce a highlighted logfmt-style string for *record*."""
    parts: List[str] = []
    key_set = set(keys) if keys else set()
    for k, v in record.items():
        key_str = _wrap(k, "cyan") if k in key_set else k
        val_str = str(v)
        if pattern:
            val_str = highlight_pattern(val_str, pattern, colour=colour)
        parts.append(f"{key_str}={val_str}")
    return " ".join(parts)
