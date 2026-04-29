"""CLI integration for the partition subcommand."""

import argparse
import json
import sys
from typing import List

from logslice.partition import iter_partitions, partition_records


def add_partition_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "partition",
        help="Split records into named buckets by field value.",
    )
    p.add_argument(
        "--field",
        metavar="FIELD",
        help="Field whose value determines the bucket (dot notation supported).",
    )
    p.add_argument(
        "--default-bucket",
        default="__other__",
        metavar="NAME",
        help="Bucket name for records with no matching field (default: __other__).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Emit one summary JSON line per bucket instead of all records.",
    )


def _read_records(stream) -> List[dict]:
    records = []
    for line in stream:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def run_partition(args: argparse.Namespace, stream=None, out=None) -> bool:
    if stream is None:
        stream = sys.stdin
    if out is None:
        out = sys.stdout

    if not args.field:
        print("error: --field is required for partition", file=sys.stderr)
        return False

    records = _read_records(stream)
    buckets = partition_records(records, field=args.field, default_bucket=args.default_bucket)

    for bucket_name, bucket_records in iter_partitions(buckets):
        if args.summary:
            out.write(
                json.dumps({"bucket": bucket_name, "count": len(bucket_records)}) + "\n"
            )
        else:
            for record in bucket_records:
                out.write(json.dumps({"_bucket": bucket_name, **record}) + "\n")

    return True


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="logslice-partition")
    subs = parser.add_subparsers(dest="command")
    add_partition_args(subs)
    args = parser.parse_args()
    if args.command == "partition":
        success = run_partition(args)
        sys.exit(0 if success else 1)
