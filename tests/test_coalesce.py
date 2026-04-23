"""Tests for logslice.coalesce."""

import pytest
from logslice.coalesce import (
    coalesce_fields,
    coalesce_records,
    fill_missing,
    apply_coalesce,
)


class TestCoalesceFields:
    def test_first_field_wins(self):
        r = {"a": 1, "b": 2}
        result = coalesce_fields(r, ["a", "b"], "out")
        assert result["out"] == 1

    def test_skips_none_value(self):
        r = {"a": None, "b": 2}
        result = coalesce_fields(r, ["a", "b"], "out")
        assert result["out"] == 2

    def test_skips_missing_field(self):
        r = {"b": 42}
        result = coalesce_fields(r, ["a", "b"], "out")
        assert result["out"] == 42

    def test_all_missing_uses_default(self):
        r = {"x": 9}
        result = coalesce_fields(r, ["a", "b"], "out", default="fallback")
        assert result["out"] == "fallback"

    def test_all_missing_default_none(self):
        r = {}
        result = coalesce_fields(r, ["a", "b"], "out")
        assert result["out"] is None

    def test_does_not_mutate_original(self):
        r = {"a": 1}
        coalesce_fields(r, ["a"], "out")
        assert "out" not in r

    def test_existing_fields_preserved(self):
        r = {"a": 1, "c": 99}
        result = coalesce_fields(r, ["a"], "out")
        assert result["c"] == 99

    def test_target_overwrites_existing(self):
        r = {"out": "old", "a": "new"}
        result = coalesce_fields(r, ["a"], "out")
        assert result["out"] == "new"

    def test_empty_fields_list_uses_default(self):
        r = {"a": 1}
        result = coalesce_fields(r, [], "out", default=0)
        assert result["out"] == 0


class TestCoalesceRecords:
    def test_applies_to_all_records(self):
        records = [{"a": 1}, {"b": 2}, {"a": 3, "b": 4}]
        results = list(coalesce_records(records, ["a", "b"], "out", default=-1))
        assert [r["out"] for r in results] == [1, 2, 3]

    def test_empty_input(self):
        assert list(coalesce_records([], ["a"], "out")) == []


class TestFillMissing:
    def test_fills_when_absent(self):
        r = {"b": 7}
        result = fill_missing(r, "a", ["b"])
        assert result["a"] == 7

    def test_fills_when_none(self):
        r = {"a": None, "b": 5}
        result = fill_missing(r, "a", ["b"])
        assert result["a"] == 5

    def test_leaves_existing_value_alone(self):
        r = {"a": 10, "b": 99}
        result = fill_missing(r, "a", ["b"])
        assert result["a"] == 10

    def test_does_not_mutate_original(self):
        r = {"b": 3}
        fill_missing(r, "a", ["b"])
        assert "a" not in r


class TestApplyCoalesce:
    def test_multiple_specs(self):
        records = [{"x": 1, "p": "hello"}]
        specs = [
            {"fields": ["x", "y"], "target": "val"},
            {"fields": ["p", "q"], "target": "msg", "default": ""},
        ]
        results = list(apply_coalesce(records, specs))
        assert results[0]["val"] == 1
        assert results[0]["msg"] == "hello"

    def test_empty_specs_passthrough(self):
        records = [{"a": 1}]
        results = list(apply_coalesce(records, []))
        assert results == [{"a": 1}]
