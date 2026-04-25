"""Tests for logslice.cast."""

import pytest
from logslice.cast import _cast_value, cast_field, cast_fields, apply_casts


# ---------------------------------------------------------------------------
# _cast_value
# ---------------------------------------------------------------------------

class TestCastValue:
    def test_str_to_int(self):
        assert _cast_value("42", "int") == 42

    def test_float_str_to_int_truncates(self):
        assert _cast_value("3.9", "int") == 3

    def test_str_to_float(self):
        assert _cast_value("1.5", "float") == 1.5

    def test_int_to_str(self):
        assert _cast_value(7, "str") == "7"

    def test_bool_true_variants(self):
        for v in ("true", "True", "1", "yes", "on"):
            assert _cast_value(v, "bool") is True

    def test_bool_false_variants(self):
        for v in ("false", "False", "0", "no", "off"):
            assert _cast_value(v, "bool") is False

    def test_bool_invalid_raises(self):
        with pytest.raises(ValueError):
            _cast_value("maybe", "bool")

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            _cast_value("x", "bytes")

    def test_invalid_int_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _cast_value("abc", "int")


# ---------------------------------------------------------------------------
# cast_field
# ---------------------------------------------------------------------------

class TestCastField:
    def test_basic_cast(self):
        r = cast_field({"count": "5"}, "count", "int")
        assert r["count"] == 5

    def test_missing_field_unchanged(self):
        r = cast_field({"a": "1"}, "b", "int")
        assert r == {"a": "1"}

    def test_cast_failure_uses_default(self):
        r = cast_field({"x": "bad"}, "x", "int", default=0)
        assert r["x"] == 0

    def test_cast_failure_no_default_unchanged(self):
        r = cast_field({"x": "bad"}, "x", "int")
        assert r["x"] == "bad"

    def test_does_not_mutate_original(self):
        original = {"n": "3"}
        cast_field(original, "n", "int")
        assert original["n"] == "3"


# ---------------------------------------------------------------------------
# cast_fields
# ---------------------------------------------------------------------------

class TestCastFields:
    def test_multiple_specs(self):
        r = cast_fields(
            {"a": "1", "b": "2.5", "c": "true"},
            [
                {"field": "a", "type": "int"},
                {"field": "b", "type": "float"},
                {"field": "c", "type": "bool"},
            ],
        )
        assert r == {"a": 1, "b": 2.5, "c": True}

    def test_empty_specs_unchanged(self):
        r = cast_fields({"x": "hello"}, [])
        assert r == {"x": "hello"}


# ---------------------------------------------------------------------------
# apply_casts
# ---------------------------------------------------------------------------

class TestApplyCasts:
    def test_yields_all_records(self):
        records = [{"v": "1"}, {"v": "2"}]
        result = list(apply_casts(records, [{"field": "v", "type": "int"}]))
        assert result == [{"v": 1}, {"v": 2}]

    def test_empty_input(self):
        assert list(apply_casts([], [{"field": "x", "type": "int"}])) == []
