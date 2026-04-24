"""Tests for logslice.cli_baseline."""
from __future__ import annotations

import argparse
import json
from io import StringIO
from typing import List
from unittest.mock import patch

import pytest

from logslice.cli_baseline import run_baseline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"save": None, "diff": None, "missing": None, "key": "id", "include_missing": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stdin_patch(records: List[dict]):
    lines = "\n".join(json.dumps(r) for r in records) + "\n"
    return patch("logslice.cli_baseline.sys.stdin", StringIO(lines))


def _captured_output():
    return patch("builtins.print")


# ---------------------------------------------------------------------------
# --save
# ---------------------------------------------------------------------------

class TestRunBaselineSave:
    def test_save_writes_file(self, tmp_path):
        path = str(tmp_path / "snap.jsonl")
        records = [{"id": "1"}, {"id": "2"}]
        with _stdin_patch(records):
            result = run_baseline(_make_args(save=path))
        assert result is True
        with open(path) as fh:
            lines = [json.loads(l) for l in fh if l.strip()]
        assert lines == records

    def test_save_returns_true(self, tmp_path):
        path = str(tmp_path / "snap.jsonl")
        with _stdin_patch([]):
            assert run_baseline(_make_args(save=path)) is True


# ---------------------------------------------------------------------------
# --diff
# ---------------------------------------------------------------------------

class TestRunBaselineDiff:
    def test_diff_new_record_printed(self, tmp_path, capsys):
        path = str(tmp_path / "snap.jsonl")
        from logslice.baseline import save_baseline
        save_baseline([{"id": "1", "v": 1}], path)
        stream = [{"id": "1", "v": 1}, {"id": "2", "v": 2}]
        with _stdin_patch(stream):
            run_baseline(_make_args(diff=path))
        out = capsys.readouterr().out
        lines = [json.loads(l) for l in out.strip().splitlines()]
        assert len(lines) == 1
        assert lines[0]["_baseline_status"] == "new"

    def test_diff_include_missing(self, tmp_path, capsys):
        path = str(tmp_path / "snap.jsonl")
        from logslice.baseline import save_baseline
        save_baseline([{"id": "1"}, {"id": "2"}], path)
        with _stdin_patch([{"id": "1"}]):
            run_baseline(_make_args(diff=path, include_missing=True))
        out = capsys.readouterr().out
        statuses = {json.loads(l)["_baseline_status"] for l in out.strip().splitlines()}
        assert "missing" in statuses


# ---------------------------------------------------------------------------
# --missing
# ---------------------------------------------------------------------------

class TestRunBaselineMissing:
    def test_missing_emitted(self, tmp_path, capsys):
        path = str(tmp_path / "snap.jsonl")
        from logslice.baseline import save_baseline
        save_baseline([{"id": "x"}, {"id": "y"}], path)
        with _stdin_patch([{"id": "x"}]):
            run_baseline(_make_args(missing=path))
        out = capsys.readouterr().out
        lines = [json.loads(l) for l in out.strip().splitlines()]
        assert lines[0]["id"] == "y"
        assert lines[0]["_baseline_status"] == "missing"


# ---------------------------------------------------------------------------
# no subcommand
# ---------------------------------------------------------------------------

def test_no_subcommand_returns_false(capsys):
    result = run_baseline(_make_args())
    assert result is False
