"""Tests for logslice.template."""
import pytest
from logslice.template import render_template, apply_template, format_as_template


class TestRenderTemplate:
    def test_simple_substitution(self):
        assert render_template("{level} {msg}", {"level": "INFO", "msg": "ok"}) == "INFO ok"

    def test_missing_field_uses_default(self):
        assert render_template("{missing}", {}, default="N/A") == "N/A"

    def test_missing_field_empty_string_default(self):
        assert render_template("[{level}]", {}) == "[]"

    def test_nested_field(self):
        record = {"request": {"method": "GET", "path": "/api"}}
        assert render_template("{request.method} {request.path}", record) == "GET /api"

    def test_nested_missing_intermediate(self):
        assert render_template("{a.b.c}", {"a": {}}, default="-") == "-"

    def test_no_placeholders(self):
        assert render_template("hello world", {"x": "1"}) == "hello world"

    def test_numeric_value_coerced_to_str(self):
        assert render_template("{code}", {"code": 200}) == "200"

    def test_multiple_same_placeholder(self):
        assert render_template("{x}/{x}", {"x": "a"}) == "a/a"


class TestApplyTemplate:
    def test_adds_rendered_field(self):
        records = [{"level": "INFO", "msg": "hi"}]
        result = list(apply_template(records, "{level}: {msg}"))
        assert result[0]["_rendered"] == "INFO: hi"

    def test_original_fields_preserved(self):
        records = [{"a": 1}]
        result = list(apply_template(records, "{a}"))
        assert result[0]["a"] == 1

    def test_custom_output_field(self):
        records = [{"x": "y"}]
        result = list(apply_template(records, "{x}", output_field="line"))
        assert "line" in result[0]
        assert result[0]["line"] == "y"

    def test_empty_input(self):
        assert list(apply_template([], "{x}")) == []

    def test_does_not_mutate_original(self):
        rec = {"a": "1"}
        list(apply_template([rec], "{a}"))
        assert "_rendered" not in rec


class TestFormatAsTemplate:
    def test_yields_strings(self):
        records = [{"level": "WARN", "msg": "watch out"}]
        result = list(format_as_template(records, "[{level}] {msg}"))
        assert result == ["[WARN] watch out"]

    def test_multiple_records(self):
        records = [{"n": str(i)} for i in range(3)]
        result = list(format_as_template(records, "item {n}"))
        assert result == ["item 0", "item 1", "item 2"]

    def test_empty_input(self):
        assert list(format_as_template([], "{x}")) == []
