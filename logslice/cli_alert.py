"""CLI sub-command: alert — filter records by numeric threshold rules."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Tuple

from logslice.alert import alert_records, annotate_alerts
from logslice.parser import parse_line


def _parse_rule(spec: str) -> Tuple[str, str, float]:
    """Parse a rule string like 'latency:gt:100' into (field, op, threshold)."""
    parts = spec.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"Rule must be field:op:threshold, got {spec!r}"
        )
    field, op, raw_threshold = parts
    try:
        threshold = float(raw_threshold)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Threshold must be numeric, got {raw_threshold!r}"
        )
    return field, op, threshold


def add_alert_args(parser: argparse.ArgumentParser) -> None:
    """Register alert arguments onto *parser*."""
    parser.add_argument(
        "--rule",
        dest="rules",
        metavar="FIELD:OP:THRESHOLD",
        type=_parse_rule,
        action="append",
        default=[],
        help="Threshold rule, e.g. latency:gt:200. Repeatable.",
    )
    parser.add_argument(
        "--any",
        dest="match_any",
        action="store_true",
        default=False,
        help="Fire when ANY rule matches (default: ALL must match).",
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        default=False,
        help="Pass all records through and add _alert field instead of filtering.",
    )
    parser.add_argument(
        "--label",
        default="_alert",
        help="Field name used when --annotate is set (default: _alert).",
    )


def _read_records(stream):
    for line in stream:
        line = line.rstrip("\n")
        if not line:
            continue
        rec = parse_line(line)
        if rec is not None:
            yield rec


def run_alert(args: argparse.Namespace, stream=None, out=None) -> bool:
    """Execute the alert sub-command. Return True on success."""
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    rules: List[Tuple[str, str, float]] = args.rules
    match_all = not args.match_any
    records = _read_records(stream)

    if args.annotate:
        results = annotate_alerts(records, rules, label=args.label)
    else:
        results = alert_records(records, rules, match_all=match_all)

    for record in results:
        out.write(json.dumps(record) + "\n")
    return True


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Filter log records by threshold rules.")
    add_alert_args(parser)
    args = parser.parse_args()
    run_alert(args)
