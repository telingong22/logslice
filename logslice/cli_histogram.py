"""CLI sub-command: histogram — print a field-value frequency histogram."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator

from logslice.histogram import field_histogram, render_histogram
from logslice.parser import parse_line


def add_histogram_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "histogram",
        help="Print an ASCII frequency histogram for a log field.",
    )
    p.add_argument("field", help="Field name to histogram.")
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show only the top N values (default: 10).",
    )
    p.add_argument(
        "--width",
        type=int,
        default=40,
        metavar="COLS",
        help="Bar width in characters (default: 40).",
    )
    p.add_argument(
        "--title",
        default=None,
        help="Optional histogram title.",
    )
    p.add_argument(
        "--json-out",
        action="store_true",
        help="Emit results as JSON array instead of ASCII bars.",
    )
    p.set_defaults(func=run_histogram)


def _read_records(stream) -> Iterator[dict]:
    for raw in stream:
        rec = parse_line(raw.rstrip("\n"))
        if rec is not None:
            yield rec


def run_histogram(args: argparse.Namespace, stream=None, out=None) -> bool:
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    records = list(_read_records(stream))
    data = field_histogram(records, args.field, top=args.top)

    if args.json_out:
        json.dump([{"value": v, "count": c} for v, c in data], out)
        out.write("\n")
    else:
        title = args.title or f"Histogram: {args.field}"
        out.write(render_histogram(data, width=args.width, title=title))
        out.write("\n")
    return True


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="logslice-histogram")
    subs = parser.add_subparsers()
    add_histogram_args(subs)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
