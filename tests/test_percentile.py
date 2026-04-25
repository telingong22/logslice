"""Tests for logslice.percentile."""

import pytest

from logslice.percentile import compute_percentiles, percentile_records


_RECORDS = [
    {"latency": "10"},
    {"latency": "20"},
    {"latency": "30"},
    {"latency": "40"},
    {"latency": "50"},
    {"latency": "60"},
    {"latency": "70"},
    {"latency": "80"},
    {"latency": "90"},
    {"latency": "100"},
]


class TestComputePercentiles:
    def test_p50_median(self):
        result = compute_percentiles(_RECORDS, "latency", [50])
        assert result["p50"] == pytest.approx(55.0)

    def test_p0_is_min(self):
        result = compute_percentiles(_RECORDS, "latency", [0])
        assert result["p0"] == 10.0

    def test_p100_is_max(self):
        result = compute_percentiles(_RECORDS, "latency", [100])
        assert result["p100"] == 100.0

    def test_multiple_percentiles(self):
        result = compute_percentiles(_RECORDS, "latency", [25, 50, 75])
        assert set(result.keys()) == {"p25", "p50", "p75"}
        assert result["p25"] < result["p50"] < result["p75"]

    def test_single_value(self):
        records = [{"x": "42"}]
        result = compute_percentiles(records, "x", [50])
        assert result["p50"] == 42.0

    def test_missing_field_ignored(self):
        records = [{"latency": "10"}, {"other": "99"}, {"latency": "20"}]
        result = compute_percentiles(records, "latency", [50])
        assert result["p50"] == pytest.approx(15.0)

    def test_non_numeric_field_ignored(self):
        records = [{"latency": "fast"}, {"latency": "10"}, {"latency": "20"}]
        result = compute_percentiles(records, "latency", [50])
        assert result["p50"] == pytest.approx(15.0)

    def test_empty_input_raises(self):
        with pytest.raises(ValueError, match="No numeric values"):
            compute_percentiles([], "latency", [50])

    def test_all_missing_raises(self):
        records = [{"other": "1"}, {"other": "2"}]
        with pytest.raises(ValueError, match="No numeric values"):
            compute_percentiles(records, "latency", [50])

    def test_out_of_range_percentile_raises(self):
        with pytest.raises(ValueError, match="Percentile must be between"):
            compute_percentiles(_RECORDS, "latency", [101])

    def test_negative_percentile_raises(self):
        with pytest.raises(ValueError, match="Percentile must be between"):
            compute_percentiles(_RECORDS, "latency", [-1])

    def test_float_values(self):
        records = [{"v": 1.5}, {"v": 2.5}, {"v": 3.5}]
        result = compute_percentiles(records, "v", [50])
        assert result["p50"] == pytest.approx(2.5)


class TestPercentileRecords:
    def test_yields_one_record(self):
        out = list(percentile_records(_RECORDS, "latency", [50, 90]))
        assert len(out) == 1

    def test_record_contains_field_name(self):
        out = list(percentile_records(_RECORDS, "latency", [50]))
        assert out[0]["field"] == "latency"

    def test_record_contains_percentile_keys(self):
        out = list(percentile_records(_RECORDS, "latency", [50, 99]))
        assert "p50" in out[0]
        assert "p99" in out[0]
