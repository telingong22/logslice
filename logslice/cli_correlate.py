"""CLI sub-command for correlating two log files by a shared key."""

import argparse
import json
import sys
from typing import Iterable, Iterator

from logslice.correlate import correlate_records
from logslice.parser import parse_line


def _read_records(path: str) -> Iterator[dict]:
    """Open *path* and yield parsed JSON records, skipping unparseable lines."""
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            rec = parse_line(line)
            if rec is not None:
                yield rec


def add_correlate_args(subparsers) -> None:
    """Register the ``correlate`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "correlate",
        help="Join two log files by a shared key field.",
    )
    p.add_argument("left", help="Path to the left log file.")
    p.add_argument("right", help="Path to the right log file.")
    p.add_argument(
        "--key",
        required=True,
        help="Field name to join on.",
    )
    p.add_argument(
        "--mode",
        choices=["inner", "left"],
        default="inner",
        help="Join mode: 'inner' (default) or 'left'.",
    )
    p.add_argument(
        "--prefix-left",
        default="left_",
        dest="prefix_left",
        help="Prefix for left-stream fields (default: 'left_').",
    )
    p.add_argument(
        "--prefix-right",
        default="right_",
        dest="prefix_right",
        help="Prefix for right-stream fields (default: 'right_').",
    )
    p.set_defaults(func=run_correlate)


def run_correlate(args: argparse.Namespace, out=None) -> bool:
    """Execute the correlate command; write JSON lines to *out*."""
    if out is None:
        out = sys.stdout

    left_records = _read_records(args.left)
    right_records = list(_read_records(args.right))  # index the right side

    results = correlate_records(
        left_records,
        right_records,
        key=args.key,
        mode=args.mode,
        prefix_left=args.prefix_left,
        prefix_right=args.prefix_right,
    )

    for rec in results:
        out.write(json.dumps(rec) + "\n")

    return True


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="logslice-correlate",
        description="Correlate two structured log files by a shared key.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_correlate_args(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
