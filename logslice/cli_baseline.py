"""CLI sub-commands for baseline comparison."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.baseline import (
    diff_against_baseline,
    load_baseline,
    missing_from_stream,
    save_baseline,
)


def add_baseline_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("baseline", help="Compare log stream against a saved baseline")
    p.add_argument("--save", metavar="FILE", help="Save stdin records as a new baseline file")
    p.add_argument("--diff", metavar="FILE", help="Diff stdin records against baseline FILE")
    p.add_argument("--missing", metavar="FILE", help="Report baseline records absent from stdin")
    p.add_argument(
        "--key", default="id", metavar="FIELD",
        help="Field used to identify records (default: id)",
    )
    p.add_argument(
        "--include-missing", action="store_true",
        help="When using --diff, also emit records missing from stream",
    )


def _read_stdin() -> List[dict]:
    records = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def run_baseline(args: argparse.Namespace) -> bool:
    if args.save:
        records = _read_stdin()
        n = save_baseline(records, args.save)
        print(json.dumps({"saved": n, "path": args.save}))
        return True

    if args.diff:
        baseline = load_baseline(args.diff)
        records = _read_stdin()
        for rec in diff_against_baseline(records, baseline, args.key):
            print(json.dumps(rec))
        if args.include_missing:
            for rec in missing_from_stream(records, baseline, args.key):
                print(json.dumps(rec))
        return True

    if args.missing:
        baseline = load_baseline(args.missing)
        records = _read_stdin()
        for rec in missing_from_stream(records, baseline, args.key):
            print(json.dumps(rec))
        return True

    print("baseline: specify --save, --diff, or --missing", file=sys.stderr)
    return False


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="logslice-baseline")
    subs = parser.add_subparsers(dest="command")
    add_baseline_args(subs)
    args = parser.parse_args()
    if not run_baseline(args):
        sys.exit(1)
