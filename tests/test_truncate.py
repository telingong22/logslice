"""Tests for logslice.truncate."""

import pytest
from logslice.truncate import (
    apply_truncation,
    truncate_all,
    truncate_fields,
    truncate_value,
)


class TestTruncateValue:
    def test_short_string_unchanged(self):
        assert truncate_value("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert truncate_value("hello", 5) == "hello"

    def test_long_string_truncated(self):
        result = truncate_value("hello world", 8)
        assert result == "hello..."
        assert len(result) == 8

    def test_custom_suffix(self):
        result = truncate_value("abcdefgh", 5, suffix="!")
        assert result == "abcd!"

    def test_non_string_unchanged(self):
        assert truncate_value(42, 3) == 42
        assert truncate_value(None, 3) is None
        assert truncate_value([1, 2, 3], 2) == [1, 2, 3]

    def test_max_length_shorter_than_suffix(self):
        result = truncate_value("abcdef", 2, suffix="...")
        assert result == "..."


class TestTruncateFields:
    def test_truncates_specified_field(self):
        rec = {"msg": "a very long message", "level": "info"}
        result = truncate_fields(rec, ["msg"], 10)
        assert result["msg"] == "a very ..."
        assert result["level"] == "info"

    def test_missing_field_ignored(self):
        rec = {"level": "info"}
        result = truncate_fields(rec, ["msg"], 10)
        assert result == {"level": "info"}

    def test_does_not_mutate_original(self):
        rec = {"msg": "hello world long string"}
        truncate_fields(rec, ["msg"], 5)
        assert rec["msg"] == "hello world long string"


class TestTruncateAll:
    def test_truncates_all_strings(self):
        rec = {"a": "long value here", "b": "short"}
        result = truncate_all(rec, 8)
        assert result["a"] == "long ..."
        assert result["b"] == "short"

    def test_skip_fields_untouched(self):
        rec = {"a": "long value here", "b": "long value here"}
        result = truncate_all(rec, 8, skip=["b"])
        assert result["a"] == "long ..."
        assert result["b"] == "long value here"

    def test_non_string_fields_untouched(self):
        rec = {"count": 999, "msg": "hello world"}
        result = truncate_all(rec, 5)
        assert result["count"] == 999


class TestApplyTruncation:
    def test_fields_mode(self):
        records = [{"msg": "hello world", "level": "info"}]
        result = list(apply_truncation(records, fields=["msg"], max_length=8))
        assert result[0]["msg"] == "hello..."
        assert result[0]["level"] == "info"

    def test_all_mode(self):
        records = [{"a": "long string here", "b": "ok"}]
        result = list(apply_truncation(records, max_length=7))
        assert result[0]["a"] == "long..."
        assert result[0]["b"] == "ok"

    def test_empty_input(self):
        assert list(apply_truncation([], max_length=10)) == []
