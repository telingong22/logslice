"""Unit tests for logslice.resample."""

import pytest
from logslice.resample import _floor_to_bucket, resample_records
from datetime import datetime, timezone


def _r(ts, **kwargs):
    return {"timestamp": ts, **kwargs}


# ---------------------------------------------------------------------------
# _floor_to_bucket
# ---------------------------------------------------------------------------

class TestFloorToBucket:
    def test_already_on_boundary(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = _floor_to_bucket(dt, 60)
        assert result == dt

    def test_mid_minute_floors_down(self):
        dt = datetime(2024, 1, 1, 12, 0, 45, tzinfo=timezone.utc)
        expected = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert _floor_to_bucket(dt, 60) == expected

    def test_five_minute_bucket(self):
        dt = datetime(2024, 1, 1, 12, 7, 30, tzinfo=timezone.utc)
        expected = datetime(2024, 1, 1, 12, 5, 0, tzinfo=timezone.utc)
        assert _floor_to_bucket(dt, 300) == expected


# ---------------------------------------------------------------------------
# resample_records — count
# ---------------------------------------------------------------------------

class TestResampleCount:
    def test_empty_input(self):
        assert list(resample_records([], 60)) == []

    def test_single_record(self):
        records = [_r("2024-01-01T12:00:30Z")]
        result = list(resample_records(records, 60))
        assert len(result) == 1
        assert result[0]["count"] == 1
        assert result[0]["bucket"] == "2024-01-01T12:00:00+00:00"

    def test_two_records_same_bucket(self):
        records = [_r("2024-01-01T12:00:10Z"), _r("2024-01-01T12:00:50Z")]
        result = list(resample_records(records, 60))
        assert len(result) == 1
        assert result[0]["count"] == 2

    def test_two_records_different_buckets(self):
        records = [_r("2024-01-01T12:00:10Z"), _r("2024-01-01T12:01:10Z")]
        result = list(resample_records(records, 60))
        assert len(result) == 2
        assert result[0]["count"] == 1
        assert result[1]["count"] == 1

    def test_missing_timestamp_skipped(self):
        records = [{"msg": "no ts"}, _r("2024-01-01T12:00:10Z")]
        result = list(resample_records(records, 60))
        assert len(result) == 1
        assert result[0]["count"] == 1

    def test_buckets_sorted_ascending(self):
        records = [_r("2024-01-01T12:02:00Z"), _r("2024-01-01T12:00:00Z")]
        result = list(resample_records(records, 60))
        assert result[0]["bucket"] < result[1]["bucket"]


# ---------------------------------------------------------------------------
# resample_records — numeric aggregations
# ---------------------------------------------------------------------------

class TestResampleAggregations:
    def _records(self):
        return [
            _r("2024-01-01T12:00:10Z", latency=10),
            _r("2024-01-01T12:00:20Z", latency=20),
            _r("2024-01-01T12:00:30Z", latency=30),
        ]

    def test_sum(self):
        result = list(resample_records(self._records(), 60, agg="sum", value_field="latency"))
        assert result[0]["sum"] == 60.0

    def test_avg(self):
        result = list(resample_records(self._records(), 60, agg="avg", value_field="latency"))
        assert result[0]["avg"] == pytest.approx(20.0)

    def test_min(self):
        result = list(resample_records(self._records(), 60, agg="min", value_field="latency"))
        assert result[0]["min"] == 10.0

    def test_max(self):
        result = list(resample_records(self._records(), 60, agg="max", value_field="latency"))
        assert result[0]["max"] == 30.0

    def test_invalid_value_skipped(self):
        records = [_r("2024-01-01T12:00:10Z", latency="bad"), _r("2024-01-01T12:00:20Z", latency=5)]
        result = list(resample_records(records, 60, agg="sum", value_field="latency"))
        assert result[0]["sum"] == 5.0
        assert result[0]["count"] == 2


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestResampleValidation:
    def test_invalid_interval(self):
        with pytest.raises(ValueError, match="positive"):
            list(resample_records([], 0))

    def test_unknown_agg(self):
        with pytest.raises(ValueError, match="Unknown aggregation"):
            list(resample_records([], 60, agg="median"))

    def test_missing_value_field_for_sum(self):
        with pytest.raises(ValueError, match="value_field"):
            list(resample_records([], 60, agg="sum"))
