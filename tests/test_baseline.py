"""Tests for logslice.baseline."""
from __future__ import annotations

import json
import os
import tempfile
from typing import List

import pytest

from logslice.baseline import (
    diff_against_baseline,
    load_baseline,
    missing_from_stream,
    save_baseline,
)

Record = dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _records(data: List[dict]) -> List[Record]:
    return data


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_round_trip(self, tmp_path):
        recs = [{"id": "1", "level": "info"}, {"id": "2", "level": "error"}]
        path = str(tmp_path / "snap.jsonl")
        n = save_baseline(recs, path)
        assert n == 2
        loaded = load_baseline(path)
        assert loaded == recs

    def test_empty_file(self, tmp_path):
        path = str(tmp_path / "empty.jsonl")
        save_baseline([], path)
        assert load_baseline(path) == []

    def test_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "a" / "b" / "snap.jsonl")
        save_baseline([{"x": 1}], path)
        assert os.path.exists(path)


# ---------------------------------------------------------------------------
# diff_against_baseline
# ---------------------------------------------------------------------------

class TestDiffAgainstBaseline:
    def test_new_record_emitted(self):
        baseline = [{"id": "1", "v": 10}]
        stream = [{"id": "1", "v": 10}, {"id": "2", "v": 20}]
        result = list(diff_against_baseline(stream, baseline, "id"))
        assert len(result) == 1
        assert result[0]["id"] == "2"
        assert result[0]["_baseline_status"] == "new"

    def test_changed_record_emitted(self):
        baseline = [{"id": "1", "v": 10}]
        stream = [{"id": "1", "v": 99}]
        result = list(diff_against_baseline(stream, baseline, "id"))
        assert result[0]["_baseline_status"] == "changed"
        assert result[0]["v"] == 99

    def test_unchanged_record_not_emitted(self):
        baseline = [{"id": "1", "v": 10}]
        stream = [{"id": "1", "v": 10}]
        assert list(diff_against_baseline(stream, baseline, "id")) == []

    def test_record_without_key_always_new(self):
        baseline = [{"id": "1"}]
        stream = [{"level": "info"}]
        result = list(diff_against_baseline(stream, baseline, "id"))
        assert result[0]["_baseline_status"] == "new"

    def test_empty_baseline_all_new(self):
        stream = [{"id": str(i)} for i in range(3)]
        result = list(diff_against_baseline(stream, [], "id"))
        assert all(r["_baseline_status"] == "new" for r in result)
        assert len(result) == 3

    def test_does_not_mutate_input(self):
        baseline = [{"id": "1", "v": 1}]
        rec = {"id": "1", "v": 2}
        list(diff_against_baseline([rec], baseline, "id"))
        assert "_baseline_status" not in rec


# ---------------------------------------------------------------------------
# missing_from_stream
# ---------------------------------------------------------------------------

class TestMissingFromStream:
    def test_detects_missing(self):
        baseline = [{"id": "1"}, {"id": "2"}]
        stream = [{"id": "1"}]
        result = missing_from_stream(stream, baseline, "id")
        assert len(result) == 1
        assert result[0]["id"] == "2"
        assert result[0]["_baseline_status"] == "missing"

    def test_none_missing(self):
        baseline = [{"id": "1"}]
        stream = [{"id": "1"}]
        assert missing_from_stream(stream, baseline, "id") == []

    def test_empty_stream_all_missing(self):
        baseline = [{"id": "a"}, {"id": "b"}]
        result = missing_from_stream([], baseline, "id")
        assert {r["id"] for r in result} == {"a", "b"}
