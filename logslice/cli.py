"""CLI entry point for logslice."""
import argparse
import sys
from typing import List, Optional

from logslice.filters import extract_timestamp, in_time_range, match_pattern
from logslice.output import FORMAT_JSON, FORMAT_LOGFMT, FORMAT_PRETTY, write_records
from logslice.parser import parse_line


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Filter and slice structured log files by time range and field patterns.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument("--from", dest="from_time", metavar="TIME", help="Start of time range (ISO8601)")
    p.add_argument("--to", dest="to_time", metavar="TIME", help="End of time range (ISO8601)")
    p.add_argument(
        "--match",
        metavar="FIELD=PATTERN",
        action="append",
        default=[],
        help="Field pattern filter, e.g. level=error (repeatable)",
    )
    p.add_argument(
        "--format",
        choices=[FORMAT_JSON, FORMAT_LOGFMT, FORMAT_PRETTY],
        default=FORMAT_JSON,
        help="Output format (default: json)",
    )
    p.add_argument("--limit", type=int, default=None, help="Max records to output")
    p.add_argument("--ts-field", default=None, help="Timestamp field name override")
    return p


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    infile = open(args.file) if args.file else sys.stdin

    try:
        patterns = {}
        for m in args.match:
            if "=" not in m:
                print(f"Invalid --match value: {m!r} (expected FIELD=PATTERN)", file=sys.stderr)
                return 2
            field, pattern = m.split("=", 1)
            patterns[field] = pattern

        matched = []
        for line in infile:
            record = parse_line(line)
            if record is None:
                continue
            ts = extract_timestamp(record, field=args.ts_field)
            if not in_time_range(ts, args.from_time, args.to_time):
                continue
            if not all(match_pattern(record, f, p) for f, p in patterns.items()):
                continue
            matched.append(record)

        write_records(matched, fmt=args.format, limit=args.limit)
        return 0
    finally:
        if args.file:
            infile.close()


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
