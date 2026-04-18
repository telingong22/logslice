"""Command-line interface for logslice."""
import argparse
import json
import sys
from typing import List, Optional

from logslice.aggregator import count_by, group_by, summarise, top_n
from logslice.filters import extract_timestamp, in_time_range, match_pattern
from logslice.output import format_record, write_records
from logslice.parser import parse_line


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Filter and slice structured log files by time range and field patterns.",
    )
    p.add_argument("file", nargs="?", help="Input log file (default: stdin)")
    p.add_argument("--from", dest="from_time", metavar="TIME", help="Start of time range (ISO-8601)")
    p.add_argument("--to", dest="to_time", metavar="TIME", help="End of time range (ISO-8601)")
    p.add_argument("--match", metavar="FIELD=PATTERN", action="append", default=[],
                   help="Keep records where FIELD matches PATTERN (glob). Repeatable.")
    p.add_argument("--format", dest="fmt", choices=["json", "logfmt", "pretty"], default="json")
    p.add_argument("--ts-field", default="time", help="Field name that holds the timestamp")
    # Aggregation
    p.add_argument("--count-by", dest="count_by", metavar="FIELD",
                   help="Print value counts for FIELD instead of records")
    p.add_argument("--group-by", dest="group_by", metavar="FIELD",
                   help="Print record counts per group for FIELD")
    p.add_argument("--summarise", dest="summarise", metavar="FIELD",
                   help="Print numeric summary statistics for FIELD")
    p.add_argument("--top", dest="top", type=int, default=10,
                   help="Limit --count-by output to top N (default: 10)")
    return p


def run(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file:
        fh = open(args.file, "r", encoding="utf-8")
    else:
        fh = sys.stdin

    try:
        records = []
        for raw in fh:
            record = parse_line(raw)
            if record is None:
                continue
            ts = extract_timestamp(record, args.ts_field)
            if not in_time_range(ts, args.from_time, args.to_time):
                continue
            if not all(match_pattern(record, m) for m in args.match):
                continue
            records.append(record)
    finally:
        if args.file:
            fh.close()

    # Aggregation modes
    if args.count_by:
        counter = count_by(records, args.count_by)
        for value, count in top_n(counter, args.top):
            print(json.dumps({args.count_by: value, "count": count}))
        return

    if args.group_by:
        groups = group_by(records, args.group_by)
        for key, recs in sorted(groups.items()):
            print(json.dumps({args.group_by: key, "count": len(recs)}))
        return

    if args.summarise:
        stats = summarise(records, args.summarise)
        print(json.dumps({"field": args.summarise, **stats}))
        return

    write_records(records, fmt=args.fmt)


def main() -> None:  # pragma: no cover
    run()
