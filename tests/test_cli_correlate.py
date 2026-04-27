"""Tests for logslice.cli_correlate."""

import argparse
import io
import json
import os
import tempfile

import pytest

from logslice.cli_correlate import run_correlate, add_correlate_args


def _make_args(**kwargs):
    defaults = dict(
        key="id",
        mode="inner",
        prefix_left="left_",
        prefix_right="right_",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_tmp(records):
    """Write *records* as JSON lines to a temp file; return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    for rec in records:
        f.write(json.dumps(rec) + "\n")
    f.close()
    return f.name


def _parsed_output(out: io.StringIO):
    out.seek(0)
    return [json.loads(line) for line in out if line.strip()]


class TestRunCorrelate:
    def test_returns_true_on_success(self):
        left = _write_tmp([{"id": 1, "val": "L"}])
        right = _write_tmp([{"id": 1, "val": "R"}])
        try:
            args = _make_args(left=left, right=right)
            assert run_correlate(args, out=io.StringIO()) is True
        finally:
            os.unlink(left)
            os.unlink(right)

    def test_inner_join_produces_merged_record(self):
        left = _write_tmp([{"id": 1, "a": 10}])
        right = _write_tmp([{"id": 1, "b": 20}])
        out = io.StringIO()
        try:
            run_correlate(_make_args(left=left, right=right), out=out)
        finally:
            os.unlink(left)
            os.unlink(right)
        records = _parsed_output(out)
        assert len(records) == 1
        assert records[0]["left_a"] == 10
        assert records[0]["right_b"] == 20

    def test_inner_join_no_match_yields_nothing(self):
        left = _write_tmp([{"id": 1, "a": 10}])
        right = _write_tmp([{"id": 2, "b": 20}])
        out = io.StringIO()
        try:
            run_correlate(_make_args(left=left, right=right), out=out)
        finally:
            os.unlink(left)
            os.unlink(right)
        assert _parsed_output(out) == []

    def test_left_join_keeps_unmatched(self):
        left = _write_tmp([{"id": 1, "a": 10}, {"id": 99, "a": 99}])
        right = _write_tmp([{"id": 1, "b": 20}])
        out = io.StringIO()
        try:
            run_correlate(_make_args(left=left, right=right, mode="left"), out=out)
        finally:
            os.unlink(left)
            os.unlink(right)
        records = _parsed_output(out)
        assert len(records) == 2

    def test_custom_prefixes(self):
        left = _write_tmp([{"id": 1, "x": "L"}])
        right = _write_tmp([{"id": 1, "x": "R"}])
        out = io.StringIO()
        try:
            run_correlate(
                _make_args(left=left, right=right, prefix_left="l_", prefix_right="r_"),
                out=out,
            )
        finally:
            os.unlink(left)
            os.unlink(right)
        records = _parsed_output(out)
        assert "l_x" in records[0]
        assert "r_x" in records[0]

    def test_add_correlate_args_registers_subcommand(self):
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        add_correlate_args(subs)
        args = parser.parse_args(["correlate", "l.log", "r.log", "--key", "id"])
        assert args.key == "id"
        assert args.mode == "inner"
