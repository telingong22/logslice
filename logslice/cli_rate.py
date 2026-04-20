"""CLI sub-command: rate — show events-per-interval for a log stream."""

from __future__ import annotations

import argparse
import json
import sys
from typing import IO, List

from logslice.rate import compute_rate


def add_rate_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rate",
        help="Compute events-per-interval from a JSON log stream.",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    p.add_argument(
        "--ts-field",
        default="timestamp",
        metavar="FIELD",
        help="Record field containing a Unix timestamp (default: timestamp).",
    )
    p.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json).",
    )
    p.set_defaults(func=run_rate)


def _read_records(stream: IO[str]) -> List[dict]:
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


def run_rate(args: argparse.Namespace, stream: IO[str] = sys.stdin) -> bool:
    records = _read_records(stream)
    rate_data = compute_rate(
        records,
        interval_seconds=args.interval,
        ts_field=args.ts_field,
    )
    for row in rate_data:
        if args.format == "json":
            print(json.dumps(row))
        else:
            print(
                f"bucket={row['bucket']:.0f}  count={row['count']}  "
                f"rate_per_sec={row['rate_per_sec']}"
            )
    return True


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="logslice-rate")
    subs = parser.add_subparsers()
    add_rate_args(subs)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
