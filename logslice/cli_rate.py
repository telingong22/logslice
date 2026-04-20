"""CLI integration for the rate subcommand.

Exposes --rate-field, --interval, --start, --end and --format options
so users can compute per-interval event rates directly from the CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable, Iterator

from logslice.parser import parse_line
from logslice.rate import compute_rate, rate_records


def add_rate_args(parser: argparse.ArgumentParser) -> None:
    """Attach rate-specific arguments to *parser*."""
    parser.add_argument(
        "--rate-field",
        default="timestamp",
        metavar="FIELD",
        help="Field used to bucket events (default: timestamp).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    parser.add_argument(
        "--start",
        default=None,
        metavar="ISO_DATETIME",
        help="Discard events before this timestamp.",
    )
    parser.add_argument(
        "--end",
        default=None,
        metavar="ISO_DATETIME",
        help="Discard events after this timestamp.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: json (default) or text.",
    )


def _read_records(stream: Iterable[str]) -> Iterator[dict]:
    """Yield parsed records from *stream*, skipping unparseable lines."""
    for line in stream:
        record = parse_line(line)
        if record is not None:
            yield record


def run_rate(args: argparse.Namespace, stream: Iterable[str] | None = None) -> bool:
    """Execute the rate subcommand.

    Reads records from *stream* (or ``sys.stdin`` when *stream* is ``None``),
    computes per-interval counts and writes results to ``sys.stdout``.

    Returns ``True`` on success.
    """
    if stream is None:
        stream = sys.stdin

    records = list(_read_records(stream))

    buckets = compute_rate(
        records,
        field=args.rate_field,
        interval=args.interval,
        start=getattr(args, "start", None),
        end=getattr(args, "end", None),
    )

    rate_recs = list(rate_records(buckets))

    fmt = getattr(args, "format", "json")
    for rec in rate_recs:
        if fmt == "json":
            sys.stdout.write(json.dumps(rec) + "\n")
        else:
            bucket = rec.get("bucket", "")
            count = rec.get("count", 0)
            rate = rec.get("rate", 0.0)
            sys.stdout.write(f"{bucket}  count={count}  rate={rate:.4f}/s\n")

    return True


def main() -> None:  # pragma: no cover
    """Standalone entry point for ``logslice-rate``."""
    parser = argparse.ArgumentParser(
        prog="logslice-rate",
        description="Compute per-interval event rates from structured log streams.",
    )
    add_rate_args(parser)
    args = parser.parse_args()
    run_rate(args)
