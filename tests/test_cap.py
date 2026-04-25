"""Tests for logslice.cap."""

import pytest
from logslice.cap import apply_caps, cap_field, cap_fields


class TestCapField:
    def test_clamps_above_max(self):
        r = {"latency": 500}
        result = cap_field(r, "latency", maximum=200)
        assert result["latency"] == 200

    def test_clamps_below_min(self):
        r = {"score": -10}
        result = cap_field(r, "score", minimum=0)
        assert result["score"] == 0

    def test_within_range_unchanged(self):
        r = {"score": 50}
        result = cap_field(r, "score", minimum=0, maximum=100)
        assert result["score"] == 50

    def test_exactly_at_max_unchanged(self):
        r = {"v": 100}
        result = cap_field(r, "v", maximum=100)
        assert result["v"] == 100

    def test_exactly_at_min_unchanged(self):
        r = {"v": 0}
        result = cap_field(r, "v", minimum=0)
        assert result["v"] == 0

    def test_non_numeric_unchanged(self):
        r = {"level": "high"}
        result = cap_field(r, "level", maximum=10)
        assert result["level"] == "high"

    def test_missing_field_unchanged(self):
        r = {"other": 5}
        result = cap_field(r, "missing", maximum=10)
        assert "missing" not in result

    def test_does_not_mutate_original(self):
        r = {"v": 999}
        cap_field(r, "v", maximum=100)
        assert r["v"] == 999

    def test_float_value_clamped(self):
        r = {"ratio": 1.75}
        result = cap_field(r, "ratio", maximum=1.0)
        assert result["ratio"] == pytest.approx(1.0)

    def test_nested_field_clamped(self):
        r = {"metrics": {"cpu": 150}}
        result = cap_field(r, "metrics.cpu", maximum=100)
        assert result["metrics"]["cpu"] == 100


class TestCapFields:
    def test_multiple_specs(self):
        r = {"a": 200, "b": -5}
        specs = [
            {"field": "a", "max": 100},
            {"field": "b", "min": 0},
        ]
        result = cap_fields(r, specs)
        assert result["a"] == 100
        assert result["b"] == 0

    def test_empty_specs_unchanged(self):
        r = {"x": 999}
        result = cap_fields(r, [])
        assert result["x"] == 999

    def test_spec_without_bounds_unchanged(self):
        r = {"x": 42}
        result = cap_fields(r, [{"field": "x"}])
        assert result["x"] == 42


class TestApplyCaps:
    def test_applies_to_all_records(self):
        records = [{"v": 200}, {"v": 50}, {"v": -10}]
        specs = [{"field": "v", "min": 0, "max": 100}]
        results = list(apply_caps(records, specs))
        assert [r["v"] for r in results] == [100, 50, 0]

    def test_empty_input(self):
        assert list(apply_caps([], [{"field": "v", "max": 10}])) == []
