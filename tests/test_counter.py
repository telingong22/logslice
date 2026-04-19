"""Tests for logslice.counter."""
import pytest
from logslice.counter import (
    count_lines,
    count_field_values,
    count_per_interval,
    annotate_index,
)


RECORDS = [
    {"level": "info", "time": "1000"},
    {"level": "warn", "time": "1045"},
    {"level": "info", "time": "1090"},
    {"level": "error", "time": "1200"},
    {"level", "time": "1250"},
]


class TestCountLines:
    def test_basic(self):
        assert count_lines(iter(RECORDS)) == 5

    def test_empty(self):
        assert count_lines([]) == 0


class TestCountFieldValues:
    def test_counts_correctly(self):
        c = count_field_values(RECORDS, "level")
        assert c["info"] == 3
        assert c["warn"] == 1
        assert c["error"] == 1

    def test_missing_field_skipped(self):
        records = [{"a": 1}, {"level": "info"}, {"level": "info"}]
        c = count_field_values(records, "level")
        assert c["info"] == 2
        assert len(c) == 1

    def test_empty_input(self):
        assert count_field_values([], "level") == {}


class TestCountPerInterval:
    def test_60s_buckets(self):
        buckets = count_per_interval(RECORDS, ts_field="time", interval=60)
        # 1000,1045 -> bucket 960; 1090 -> bucket 1080; 1200,1250 -> bucket 1200
        assert buckets[960] == 2
        assert buckets[1080] == 1
        assert buckets[1200] == 2

    def test_missing_ts_skipped(self):
        records = [{"x": 1}, {"time": "100"}, {"time": "bad"}]
        buckets = count_per_interval(records, interval=60)
        assert sum(buckets.values()) == 1

    def test_empty_input(self):
        assert count_per_interval([]) == {}


class TestAnnotateIndex:
    def test_default_start(self):
        out = list(annotate_index([{"a": 1}, {"a": 2}]))
        assert out[0]["_index"] == 0
        assert out[1]["_index"] == 1

    def test_custom_start(self):
        out = list(annotate_index([{"a": 1}], start=5))
        assert out[0]["_index"] == 5

    def test_custom_field(self):
        out = list(annotate_index([{"a": 1}], field="n"))
        assert "n" in out[0]

    def test_does_not_mutate_original(self):
        rec = {"a": 1}
        list(annotate_index([rec]))
        assert "_index" not in rec
