"""Tests for logslice.validate."""
import pytest
from logslice.validate import (
    validate_required,
    validate_type,
    validate_allowed_values,
    validate_record,
    filter_valid,
)


class TestValidateRequired:
    def test_all_present(self):
        assert validate_required({"a": 1, "b": 2}, ["a", "b"]) == []

    def test_missing_one(self):
        assert validate_required({"a": 1}, ["a", "b"]) == ["b"]

    def test_empty_required(self):
        assert validate_required({"a": 1}, []) == []

    def test_empty_record(self):
        assert validate_required({}, ["x"]) == ["x"]


class TestValidateType:
    def test_correct_type(self):
        assert validate_type({"level": "info"}, "level", str) is True

    def test_wrong_type(self):
        assert validate_type({"count": "5"}, "count", int) is False

    def test_missing_field(self):
        assert validate_type({}, "level", str) is False

    def test_int_correct(self):
        assert validate_type({"n": 3}, "n", int) is True


class TestValidateAllowedValues:
    def test_value_allowed(self):
        assert validate_allowed_values({"level": "info"}, "level", ["info", "warn"]) is True

    def test_value_not_allowed(self):
        assert validate_allowed_values({"level": "trace"}, "level", ["info", "warn"]) is False

    def test_missing_field(self):
        assert validate_allowed_values({}, "level", ["info"]) is False


class TestValidateRecord:
    def test_no_errors(self):
        rec = {"level": "info", "msg": "ok", "code": 200}
        errors = validate_record(
            rec,
            required=["level", "msg"],
            types={"code": int},
            allowed={"level": ["info", "warn", "error"]},
        )
        assert errors == []

    def test_missing_required(self):
        errors = validate_record({"level": "info"}, required=["level", "msg"])
        assert any("msg" in e for e in errors)

    def test_wrong_type_error(self):
        errors = validate_record({"code": "200"}, types={"code": int})
        assert any("code" in e for e in errors)

    def test_disallowed_value_error(self):
        errors = validate_record({"level": "trace"}, allowed={"level": ["info", "warn"]})
        assert any("level" in e for e in errors)


class TestFilterValid:
    def test_keeps_valid(self):
        records = [{"level": "info"}, {"level": "warn"}, {"level": "trace"}]
        result = list(filter_valid(records, allowed={"level": ["info", "warn"]}))
        assert len(result) == 2

    def test_empty_input(self):
        assert list(filter_valid([], required=["level"])) == []

    def test_all_invalid(self):
        records = [{"x": 1}, {"x": 2}]
        result = list(filter_valid(records, required=["level"]))
        assert result == []
