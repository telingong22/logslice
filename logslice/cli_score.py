"""CLI integration for the scoring module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.score import score_field_match, threshold_filter, top_scoring


def _parse_rule(spec: str):
    """Parse a rule spec of the form ``field=value:weight``."""
    try:
        lhs, weight_str = spec.rsplit(":", 1)
        field, value = lhs.split("=", 1)
        weight = float(weight_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid rule spec {spec!r}. Expected field=value:weight"
        )
    # Try to coerce value to a number for numeric comparisons.
    for coerce in (int, float):
        try:
            value = coerce(value)  # type: ignore[assignment]
            break
        except ValueError:
            pass
    return (field, value, weight)


def add_score_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--rule",
        dest="rules",
        metavar="field=value:weight",
        action="append",
        default=[],
        type=_parse_rule,
        help="Scoring rule (repeatable).",
    )
    parser.add_argument(
        "--base",
        type=float,
        default=0.0,
        help="Base score applied to every record (default: 0).",
    )
    parser.add_argument(
        "--score-field",
        default="_score",
        help="Output field name for the score (default: _score).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Discard records with score below this threshold.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Return only the top N highest-scoring records.",
    )


def _read_records(stream):
    for line in stream:
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                pass


def run_score(args: argparse.Namespace, stream=None, out=None) -> bool:
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    records = _read_records(stream)
    scored = score_field_match(records, args.rules, score_field=args.score_field, base=args.base)
    filtered = threshold_filter(scored, min_score=args.min_score, score_field=args.score_field)

    if args.top is not None:
        results = top_scoring(filtered, n=args.top, score_field=args.score_field)
    else:
        results = list(filtered)

    for record in results:
        out.write(json.dumps(record) + "\n")
    return True


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Score and rank log records.")
    add_score_args(parser)
    args = parser.parse_args(argv)
    run_score(args)


if __name__ == "__main__":  # pragma: no cover
    main()
