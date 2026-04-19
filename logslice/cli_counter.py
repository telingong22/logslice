"""CLI helpers for the --count family of options."""
import argparse
import json
import sys
from typing import List, IO

from logslice.counter import (
    count_lines,
    count_field_values,
    count_per_interval,
    annotate_index,
)
from logslice.parser import parse_line


def add_counter_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("counting")
    g.add_argument("--count", action="store_true", help="Print total record count and exit")
    g.add_argument("--count-by", metavar="FIELD", help="Print value frequencies for FIELD")
    g.add_argument(
        "--count-interval",
        metavar="SECONDS",
        type=int,
        default=None,
        help="Bucket records by timestamp interval and print counts",
    )
    g.add_argument(
        "--annotate-index",
        metavar="FIELD",
        nargs="?",
        const="_index",
        default=None,
        help="Add a sequential index field to each record (default field: _index)",
    )


def _read_records(stream: IO[str]) -> list:
    records = []
    for line in stream:
        line = line.rstrip("\n")
        if not line:
            continue
        rec = parse_line(line)
        if rec is not None:
            records.append(rec)
    return records


def run_counter(args: argparse.Namespace, stream: IO[str] = sys.stdin) -> bool:
    """Handle counting sub-commands.  Returns True if a counting action was taken."""
    if args.count:
        records = _read_records(stream)
        print(count_lines(records))
        return True

    if args.count_by:
        records = _read_records(stream)
        freq = count_field_values(records, args.count_by)
        for val, n in sorted(freq.items(), key=lambda x: -x[1]):
            print(json.dumps({args.count_by: val, "count": n}))
        return True

    if args.count_interval is not None:
        records = _read_records(stream)
        buckets = count_per_interval(records, interval=args.count_interval)
        for bucket in sorted(buckets):
            print(json.dumps({"bucket": bucket, "count": buckets[bucket]}))
        return True

    return False
