"""CLI sub-command: enrich — add derived fields to a log stream."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.enrich import apply_enrichments
from logslice.parser import parse_line
from logslice.output import format_record


def _parse_step(raw: str) -> dict:
    """Parse a single enrichment step from a JSON string.

    Convenience shortcuts are also supported:
      - ``static:field=value``  -> static enrichment
      - ``copy:src->dst``       -> copy enrichment
    """
    if raw.startswith("static:"):
        rest = raw[len("static:"):]
        field, _, value = rest.partition("=")
        if not field:
            raise argparse.ArgumentTypeError(f"Invalid static spec: {raw!r}")
        return {"type": "static", "field": field, "value": value}

    if raw.startswith("copy:"):
        rest = raw[len("copy:"):]
        src, _, dst = rest.partition("->")
        if not src or not dst:
            raise argparse.ArgumentTypeError(f"Invalid copy spec: {raw!r}")
        return {"type": "copy", "src": src, "dst": dst}

    # Fall back to full JSON
    try:
        step = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            f"Enrichment step must be JSON or a shortcut string: {exc}"
        ) from exc
    return step


def add_enrich_args(parser: argparse.ArgumentParser) -> None:
    """Attach enrich-specific arguments to *parser*."""
    parser.add_argument(
        "--step",
        dest="steps",
        metavar="STEP",
        action="append",
        default=[],
        help=(
            "Enrichment step. Repeat for multiple steps. "
            "Shortcuts: 'static:field=value', 'copy:src->dst'. "
            "Or pass a full JSON object."
        ),
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["json", "logfmt"],
        default="json",
        help="Output format (default: json).",
    )


def run_enrich(args: argparse.Namespace, lines: List[str]) -> bool:
    """Execute the enrich sub-command. Returns True on success."""
    steps = [_parse_step(s) for s in args.steps]

    records = (r for line in lines if (r := parse_line(line)) is not None)
    enriched = apply_enrichments(records, steps)

    for record in enriched:
        print(format_record(record, fmt=args.output_format))

    return True


def main(argv: List[str] | None = None) -> None:
    """Entry point for the enrich sub-command."""
    parser = argparse.ArgumentParser(
        prog="logslice-enrich",
        description="Add derived fields to a structured log stream.",
    )
    add_enrich_args(parser)
    args = parser.parse_args(argv)
    lines = sys.stdin.read().splitlines()
    run_enrich(args, lines)
