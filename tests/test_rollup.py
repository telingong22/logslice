"""Tests for logslice.rollup."""

import pytest
from logslice.rollup import (
    rollup_avg,
    rollup_min_max,
    rollup_records,
    rollup_sum,
)


RECORDS = [
    {"level": "info", "duration": 10, "size": 100},
    {"level": "warn", "duration": 20, "size": 200},
    {"level": "error", "duration": 30, "size": 300},
]


class TestRollupSum:
    def test_basic_sum(self):
        result = rollup_sum(RECORDS, ["duration", "size"])
        assert result["duration"] == 60.0
        assert result["size"] == 600.0

    def test_missing_field_ignored(self):
        records = [{"x": 1}, {"y": 2}, {"x": 3}]
        result = rollup_sum(records, ["x"])
        assert result["x"] == 4.0

    def test_empty_input(self):
        result = rollup_sum([], ["duration"])
        assert result["duration"] == 0.0

    def test_non_numeric_ignored(self):
        records = [{"v": "abc"}, {"v": 5}]
        result = rollup_sum(records, ["v"])
        assert result["v"] == 5.0


class TestRollupAvg:
    def test_basic_avg(self):
        result = rollup_avg(RECORDS, ["duration"])
        assert result["duration"] == pytest.approx(20.0)

    def test_empty_input_returns_none(self):
        result = rollup_avg([], ["duration"])
        assert result["duration"] is None

    def test_partial_missing(self):
        records = [{"v": 10}, {"other": 1}, {"v": 20}]
        result = rollup_avg(records, ["v"])
        assert result["v"] == pytest.approx(15.0)


class TestRollupMinMax:
    def test_min_max_values(self):
        result = rollup_min_max(RECORDS, ["duration"])
        assert result["duration"]["min"] == 10.0
        assert result["duration"]["max"] == 30.0

    def test_single_record(self):
        result = rollup_min_max([{"v": 7}], ["v"])
        assert result["v"]["min"] == 7.0
        assert result["v"]["max"] == 7.0

    def test_empty_input_returns_none(self):
        result = rollup_min_max([], ["v"])
        assert result["v"]["min"] is None
        assert result["v"]["max"] is None

    def test_all_missing_field(self):
        records = [{"other": 1}, {"other": 2}]
        result = rollup_min_max(records, ["v"])
        assert result["v"]["min"] is None
        assert result["v"]["max"] is None


class TestRollupRecords:
    def test_sum_op(self):
        out = list(rollup_records(RECORDS, ["duration"], ["sum"]))
        assert len(out) == 1
        assert out[0]["duration_sum"] == 60.0
        assert out[0]["_count"] == 3

    def test_avg_op(self):
        out = list(rollup_records(RECORDS, ["duration"], ["avg"]))
        assert out[0]["duration_avg"] == pytest.approx(20.0)

    def test_min_max_ops(self):
        out = list(rollup_records(RECORDS, ["duration"], ["min", "max"]))
        assert out[0]["duration_min"] == 10.0
        assert out[0]["duration_max"] == 30.0

    def test_all_ops_combined(self):
        out = list(rollup_records(RECORDS, ["size"], ["sum", "avg", "min", "max"]))
        r = out[0]
        assert r["size_sum"] == 600.0
        assert r["size_avg"] == pytest.approx(200.0)
        assert r["size_min"] == 100.0
        assert r["size_max"] == 300.0

    def test_empty_records_count_zero(self):
        out = list(rollup_records([], ["duration"], ["sum"]))
        assert out[0]["_count"] == 0
