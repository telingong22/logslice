"""CLI integration for pivot subcommand."""
import argparse
import json
import sys
from typing import Iterator, Dict, Any

from logslice.pivot import pivot_records
from logslice.parser import parse_line
from logslice.output import format_record


def add_pivot_args(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("pivot", help="Pivot records by key and value fields")
    p.add_argument("--key", required=True, help="Field to group by")
    p.add_argument("--value", required=True, help="Field whose values to collect")
    p.add_argument(
        "--agg",
        default="list",
        choices=["list", "count", "first", "last"],
        help="Aggregation to apply (default: list)",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        default="json",
        choices=["json", "logfmt", "pretty"],
        help="Output format (default: json)",
    )
    p.set_defaults(func=run_pivot)


def _read_records(stream) -> Iterator[Dict[str, Any]]:
    for line in stream:
        line = line.rstrip("\n")
        if not line:
            continue
        record = parse_line(line)
        if record is not None:
            yield record


def run_pivot(args: argparse.Namespace, stream=None, out=None) -> bool:
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    records = _read_records(stream)
    pivoted = pivot_records(records, args.key, args.value, args.agg)

    for record in pivoted:
        out.write(format_record(record, args.fmt) + "\n")

    return True


def main() -> None:
    parser = argparse.ArgumentParser(prog="logslice-pivot")
    subs = parser.add_subparsers()
    add_pivot_args(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)
