"""Tests for logslice.sort."""
import pytest
from logslice.sort import sort_records, sort_by_timestamp


RECORDS = [
    {"ts": "2024-01-03", "msg": "c"},
    {"ts": "2024-01-01", "msg": "a"},
    {"ts": "2024-01-02", "msg": "b"},
]


class TestSortRecords:
    def test_ascending(self):
        result = list(sort_records(RECORDS, field="ts"))
        assert [r["msg"] for r in result] == ["a", "b", "c"]

    def test_descending(self):
        result = list(sort_records(RECORDS, field="ts", reverse=True))
        assert [r["msg"] for r in result] == ["c", "b", "a"]

    def test_missing_field_last_by_default(self):
        records = [
            {"ts": "2024-01-02", "msg": "b"},
            {"msg": "no-ts"},
            {"ts": "2024-01-01", "msg": "a"},
        ]
        result = list(sort_records(records, field="ts"))
        assert result[-1]["msg"] == "no-ts"

    def test_missing_field_first_when_missing_last_false(self):
        records = [
            {"ts": "2024-01-02", "msg": "b"},
            {"msg": "no-ts"},
            {"ts": "2024-01-01", "msg": "a"},
        ]
        result = list(sort_records(records, field="ts", missing_last=False))
        assert result[0]["msg"] == "no-ts"

    def test_empty_input(self):
        assert list(sort_records([], field="ts")) == []

    def test_single_record(self):
        records = [{"ts": "2024-01-01", "val": 1}]
        assert list(sort_records(records, field="ts")) == records

    def test_stable_equal_values(self):
        records = [
            {"ts": "2024-01-01", "msg": "first"},
            {"ts": "2024-01-01", "msg": "second"},
        ]
        result = list(sort_records(records, field="ts"))
        assert len(result) == 2


class TestSortByTimestamp:
    def test_default_field(self):
        records = [
            {"timestamp": "2024-01-03"},
            {"timestamp": "2024-01-01"},
            {"timestamp": "2024-01-02"},
        ]
        result = list(sort_by_timestamp(records))
        assert result[0]["timestamp"] == "2024-01-01"
        assert result[-1]["timestamp"] == "2024-01-03"

    def test_custom_field(self):
        records = [
            {"time": "2024-01-02"},
            {"time": "2024-01-01"},
        ]
        result = list(sort_by_timestamp(records, field="time"))
        assert result[0]["time"] == "2024-01-01"

    def test_reverse(self):
        records = [
            {"timestamp": "2024-01-01"},
            {"timestamp": "2024-01-03"},
            {"timestamp": "2024-01-02"},
        ]
        result = list(sort_by_timestamp(records, reverse=True))
        assert result[0]["timestamp"] == "2024-01-03"
