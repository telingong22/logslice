"""Output formatting for logslice results."""
import json
import sys
from typing import Any, Dict, IO, List, Optional


FORMAT_JSON = "json"
FORMAT_LOGFMT = "logfmt"
FORMAT_PRETTY = "pretty"


def _to_logfmt(record: Dict[str, Any]) -> str:
    parts = []
    for key, value in record.items():
        if value is None:
            parts.append(key)
        elif isinstance(value, str) and (" " in value or "=" in value or '"' in value):
            escaped = value.replace('"', '\\"')
            parts.append(f'{key}="{escaped}"')
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)


def _to_pretty(record: Dict[str, Any]) -> str:
    lines = []
    for key, value in record.items():
        lines.append(f"  {key}: {value}")
    return "---\n" + "\n".join(lines)


def format_record(record: Dict[str, Any], fmt: str = FORMAT_JSON) -> str:
    if fmt == FORMAT_LOGFMT:
        return _to_logfmt(record)
    elif fmt == FORMAT_PRETTY:
        return _to_pretty(record)
    else:
        return json.dumps(record, default=str)


def write_records(
    records: List[Dict[str, Any]],
    fmt: str = FORMAT_JSON,
    out: Optional[IO[str]] = None,
    limit: Optional[int] = None,
) -> int:
    """Write records to output stream. Returns count of records written."""
    if out is None:
        out = sys.stdout
    count = 0
    for record in records:
        if limit is not None and count >= limit:
            break
        out.write(format_record(record, fmt) + "\n")
        count += 1
    return count
