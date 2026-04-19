"""CLI helpers for template-based output formatting."""
from __future__ import annotations
import argparse
import sys
from typing import List

from logslice.parser import parse_line
from logslice.template import format_as_template


def add_template_args(parser: argparse.ArgumentParser) -> None:
    """Add --template arguments to *parser*."""
    parser.add_argument(
        "--template",
        metavar="TMPL",
        help="Output template with {field} placeholders, e.g. '{ts} {level} {msg}'",
    )
    parser.add_argument(
        "--template-default",
        metavar="STR",
        default="",
        help="Replacement for missing fields (default: empty string)",
    )


def run_template(args: argparse.Namespace, lines: List[str]) -> bool:
    """Render each log line using the template from *args*.

    Returns True if at least one record was rendered.
    """
    if not args.template:
        return False

    records = (r for raw in lines if (r := parse_line(raw.rstrip())) is not None)
    rendered = format_as_template(records, args.template, default=args.template_default)

    count = 0
    for line in rendered:
        print(line)
        count += 1

    return count > 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="logslice-template",
        description="Render log records using a text template.",
    )
    add_template_args(parser)
    args = parser.parse_args(argv)
    lines = sys.stdin.readlines()
    run_template(args, lines)


if __name__ == "__main__":  # pragma: no cover
    main()
