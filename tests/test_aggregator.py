"""Tests for logslice.aggregator."""
import pytest
from collections import Counter
from logslice.aggregator import count_by, group_by, summarise, top_n

SAMPLE = [
    {"level": "info", "duration_ms": "120", "service": "api"},
    {"level": "error", "duration_ms": "300", "service": "api"},
    {"level": "info", "duration_ms": "80", "service": "worker"},
    {"level": "warn", "service": "api"},
    {"level": "error", "duration_ms": "450", "service": "worker"},
]


class TestCountBy:
    def test_basic_count(self):
        result = count_by(SAMPLE, "level")
        assert result["info"] == 2
        assert result["error"] == 2
        assert result["warn"] == 1

    def test_missing_field_ignored(self):
        records = [{"a": 1}, {"b": 2}, {"a": 1}]
        result = count_by(records, "a")
        assert result["1"] == 2
        assert "None" not in result

    def test_empty_input(self):
        assert count_by([], "level") == Counter()


class TestGroupBy:
    def test_groups_created(self):
        result = group_by(SAMPLE, "service")
        assert set(result.keys()) == {"api", "worker"}
        assert len(result["api"]) == 3
        assert len(result["worker"]) == 2

    def test_records_preserved(self):
        result = group_by(SAMPLE, "level")
        for rec in result["error"]:
            assert rec["level"] == "error"


class TestSummarise:
    def test_numeric_stats(self):
        result = summarise(SAMPLE, "duration_ms")
        assert result["count"] == 4
        assert result["min"] == 80.0
        assert result["max"] == 450.0
        assert result["sum"] == pytest.approx(950.0)
        assert result["mean"] == pytest.approx(237.5)

    def test_no_numeric_values(self):
        result = summarise(SAMPLE, "level")
        assert result["count"] == 0
        assert result["min"] is None

    def test_empty_input(self):
        result = summarise([], "duration_ms")
        assert result["count"] == 0


class TestTopN:
    def test_top_n_returns_correct_count(self):
        c = Counter({"a": 5, "b": 3, "c": 1})
        assert top_n(c, 2) == [("a", 5), ("b", 3)]

    def test_top_n_default_ten(self):
        c = Counter({str(i): i for i in range(20)})
        assert len(top_n(c)) == 10
