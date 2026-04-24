"""CLI sub-command: resample — bucket log records into time intervals."""

import argparse
import json
import sys
from typing import List

from logslice.resample import resample_records


def add_resample_args(subparsers) -> None:
    p = subparsers.add_parser(
        "resample",
        help="Bucket records into fixed time intervals and emit summaries.",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    p.add_argument(
        "--ts-field",
        default="timestamp",
        metavar="FIELD",
        help="Field containing the timestamp (default: timestamp).",
    )
    p.add_argument(
        "--agg",
        choices=["count", "sum", "avg", "min", "max"],
        default="count",
        help="Aggregation function (default: count).",
    )
    p.add_argument(
        "--value-field",
        default=None,
        metavar="FIELD",
        help="Numeric field to aggregate (required for sum/avg/min/max).",
    )
    p.set_defaults(func=run_resample)


def _read_records(stream) -> List[dict]:
    records = []
    for line in stream:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def run_resample(args, stream=None, out=None) -> bool:
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    records = _read_records(stream)
    try:
        results = list(
            resample_records(
                records,
                interval_seconds=args.interval,
                ts_field=args.ts_field,
                agg=args.agg,
                value_field=args.value_field,
            )
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return False

    for rec in results:
        out.write(json.dumps(rec) + "\n")
    return True


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="logslice-resample")
    subs = parser.add_subparsers()
    add_resample_args(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    ok = args.func(args)
    sys.exit(0 if ok else 1)
