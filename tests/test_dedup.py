"""Tests for logslice.dedup."""
import pytest
from logslice.dedup import dedup_records, dedup_consecutive


RECORDS = [
    {"level": "info", "msg": "started"},
    {"level": "info", "msg": "started"},
    {"level": "error", "msg": "failed"},
    {"level": "info", "msg": "started"},
]


class TestDedupRecords:
    def test_keep_first_removes_duplicates(self):
        result = list(dedup_records(RECORDS, keep="first"))
        assert result == [
            {"level": "info", "msg": "started"},
            {"level": "error", "msg": "failed"},
        ]

    def test_keep_last_returns_last_occurrence(self):
        records = [
            {"id": 1, "val": "a"},
            {"id": 1, "val": "b"},
        ]
        result = list(dedup_records(records, fields=["id"], keep="last"))
        assert result == [{"id": 1, "val": "b"}]

    def test_fields_subset_dedup(self):
        records = [
            {"level": "info", "msg": "x", "ts": 1},
            {"level": "info", "msg": "x", "ts": 2},
            {"level": "error", "msg": "y", "ts": 3},
        ]
        result = list(dedup_records(records, fields=["level", "msg"]))
        assert len(result) == 2
        assert result[0]["ts"] == 1
        assert result[1]["ts"] == 3

    def test_empty_input(self):
        assert list(dedup_records([])) == []

    def test_invalid_keep_raises(self):
        with pytest.raises(ValueError, match="keep must be"):
            list(dedup_records(RECORDS, keep="middle"))

    def test_no_duplicates_unchanged(self):
        records = [{"a": 1}, {"a": 2}, {"a": 3}]
        assert list(dedup_records(records)) == records


class TestDedupConsecutive:
    def test_removes_consecutive_only(self):
        result = list(dedup_consecutive(RECORDS))
        assert result == [
            {"level": "info", "msg": "started"},
            {"level": "error", "msg": "failed"},
            {"level": "info", "msg": "started"},
        ]

    def test_empty_input(self):
        assert list(dedup_consecutive([])) == []

    def test_all_unique(self):
        records = [{"n": i} for i in range(5)]
        assert list(dedup_consecutive(records)) == records

    def test_fields_subset(self):
        records = [
            {"level": "info", "ts": 1},
            {"level": "info", "ts": 2},
            {"level": "error", "ts": 3},
        ]
        result = list(dedup_consecutive(records, fields=["level"]))
        assert len(result) == 2
