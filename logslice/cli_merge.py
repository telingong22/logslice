"""CLI helpers for merge/diff sub-commands."""
import argparse
import sys
from typing import List

from logslice.merge import merge_files, tag_source
from logslice.diff import diff_consecutive, changed_only
from logslice.output import write_records


def add_merge_args(subparsers) -> None:
    p = subparsers.add_parser("merge", help="Merge multiple log files by timestamp")
    p.add_argument("files", nargs="+", help="Log files to merge")
    p.add_argument("--timestamp-field", default="timestamp")
    p.add_argument("--tag-source", action="store_true", help="Annotate records with source filename")
    p.add_argument("--source-field", default="_source")
    p.add_argument("--missing-last", action="store_true", default=True)
    p.add_argument("--format", choices=["json", "logfmt", "pretty"], default="json")
    p.set_defaults(func=_run_merge)


def add_diff_args(subparsers) -> None:
    p = subparsers.add_parser("diff", help="Annotate records with changed fields")
    p.add_argument("files", nargs="+")
    p.add_argument("--fields", nargs="*", default=None)
    p.add_argument("--changed-only", action="store_true")
    p.add_argument("--tag-field", default="_diff")
    p.add_argument("--format", choices=["json", "logfmt", "pretty"], default="json")
    p.set_defaults(func=_run_diff)


def _open_file(path: str):
    """Open a file for reading, exiting with a clear message if it cannot be found."""
    try:
        return open(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"error: permission denied: {path}", file=sys.stderr)
        sys.exit(1)


def _run_merge(args) -> None:
    streams = []
    for path in args.files:
        from logslice.merge import merge_files as _mf
        # read each file individually so we can tag
        from logslice.parser import parse_line

        def _read(p):
            with _open_file(p) as fh:
                for line in fh:
                    line = line.rstrip("\n")
                    if line:
                        r = parse_line(line)
                        if r is not None:
                            yield r

        stream = _read(path)
        if args.tag_source:
            stream = tag_source(stream, path, field=args.source_field)
        streams.append(stream)

    from logslice.merge import merge_streams
    records = merge_streams(streams, timestamp_field=args.timestamp_field)
    write_records(records, fmt=args.format, out=sys.stdout)


def _run_diff(args) -> None:
    from logslice.merge import merge_files
    records = merge_files(args.files)
    if args.changed_only:
        records = changed_only(records, fields=args.fields, tag_field=args.tag_field)
    else:
        records = diff_consecutive(records, fields=args.fields, tag_field=args.tag_field)
    write_records(records, fmt=args.format, out=sys.stdout)
