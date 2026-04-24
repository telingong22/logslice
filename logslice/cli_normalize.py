"""CLI sub-command: normalize — apply field normalization to a log stream."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, Iterator, List, Optional

from logslice.normalize import apply_normalizations


def add_normalize_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "normalize",
        help="Normalize field values (case, strip, type coercion)",
    )
    p.add_argument(
        "--case",
        metavar="FIELD",
        action="append",
        default=[],
        help="Field(s) to case-fold (repeatable)",
    )
    p.add_argument(
        "--case-mode",
        default="lower",
        choices=("lower", "upper", "title"),
        help="Case mode (default: lower)",
    )
    p.add_argument(
        "--strip",
        metavar="FIELD",
        action="append",
        default=[],
        help="Field(s) to strip whitespace from (repeatable)",
    )
    p.add_argument(
        "--strip-chars",
        default=None,
        metavar="CHARS",
        help="Characters to strip (default: whitespace)",
    )
    p.add_argument(
        "--coerce",
        metavar="FIELD:TYPE",
        action="append",
        default=[],
        help="Coerce field to type, e.g. status:int (repeatable)",
    )
    p.set_defaults(func=run_normalize)


def _parse_coerce_specs(specs: List[str]) -> Dict[str, str]:
    type_map: Dict[str, str] = {}
    for spec in specs:
        if ":" not in spec:
            raise argparse.ArgumentTypeError(
                f"Invalid --coerce spec {spec!r}; expected FIELD:TYPE"
            )
        field, _, typename = spec.partition(":")
        type_map[field.strip()] = typename.strip()
    return type_map


def _read_records(stream) -> Iterator[Dict]:
    for line in stream:
        line = line.rstrip("\n")
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            pass


def run_normalize(args: argparse.Namespace, stream=None, out=None) -> bool:
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    type_map = _parse_coerce_specs(args.coerce)

    records = apply_normalizations(
        _read_records(stream),
        case_fields=args.case or None,
        case_mode=args.case_mode,
        strip_fields=args.strip or None,
        strip_chars=args.strip_chars,
        type_map=type_map or None,
    )
    for record in records:
        out.write(json.dumps(record) + "\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(prog="logslice-normalize")
    subs = parser.add_subparsers()
    add_normalize_args(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)
