"""Tests for logslice.normalize."""

import pytest

from logslice.normalize import (
    apply_normalizations,
    normalize_case,
    normalize_coerce,
    normalize_strip,
)


# ---------------------------------------------------------------------------
# normalize_case
# ---------------------------------------------------------------------------

class TestNormalizeCase:
    def test_lower(self):
        rec = {"level": "ERROR", "msg": "Hello World"}
        result = normalize_case(rec, ["level", "msg"], mode="lower")
        assert result == {"level": "error", "msg": "hello world"}

    def test_upper(self):
        rec = {"level": "info"}
        assert normalize_case(rec, ["level"], mode="upper") == {"level": "INFO"}

    def test_title(self):
        rec = {"name": "john doe"}
        assert normalize_case(rec, ["name"], mode="title") == {"name": "John Doe"}

    def test_missing_field_ignored(self):
        rec = {"a": "Hello"}
        result = normalize_case(rec, ["a", "b"], mode="lower")
        assert result == {"a": "hello"}

    def test_non_string_field_skipped(self):
        rec = {"count": 42}
        result = normalize_case(rec, ["count"], mode="lower")
        assert result["count"] == 42

    def test_does_not_mutate_original(self):
        rec = {"level": "ERROR"}
        normalize_case(rec, ["level"])
        assert rec["level"] == "ERROR"

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            normalize_case({"x": "y"}, ["x"], mode="camel")


# ---------------------------------------------------------------------------
# normalize_strip
# ---------------------------------------------------------------------------

class TestNormalizeStrip:
    def test_strips_whitespace(self):
        rec = {"msg": "  hello  "}
        assert normalize_strip(rec, ["msg"]) == {"msg": "hello"}

    def test_strips_custom_chars(self):
        rec = {"path": "/foo/bar/"}
        assert normalize_strip(rec, ["path"], chars="/") == {"path": "foo/bar"}

    def test_non_string_skipped(self):
        rec = {"n": 5}
        assert normalize_strip(rec, ["n"]) == {"n": 5}

    def test_does_not_mutate(self):
        rec = {"x": "  hi  "}
        normalize_strip(rec, ["x"])
        assert rec["x"] == "  hi  "


# ---------------------------------------------------------------------------
# normalize_coerce
# ---------------------------------------------------------------------------

class TestNormalizeCoerce:
    def test_str_to_int(self):
        rec = {"code": "404"}
        assert normalize_coerce(rec, {"code": "int"}) == {"code": 404}

    def test_str_to_float(self):
        rec = {"latency": "1.5"}
        result = normalize_coerce(rec, {"latency": "float"})
        assert result["latency"] == pytest.approx(1.5)

    def test_truthy_bool_coerce(self):
        for val in ("true", "1", "yes"):
            assert normalize_coerce({"flag": val}, {"flag": "bool"})["flag"] is True

    def test_falsy_bool_coerce(self):
        for val in ("false", "0", "no"):
            assert normalize_coerce({"flag": val}, {"flag": "bool"})["flag"] is False

    def test_invalid_coerce_leaves_unchanged(self):
        rec = {"n": "abc"}
        assert normalize_coerce(rec, {"n": "int"}) == {"n": "abc"}

    def test_missing_field_ignored(self):
        rec = {"a": "1"}
        result = normalize_coerce(rec, {"a": "int", "b": "int"})
        assert result == {"a": 1}

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown type"):
            normalize_coerce({"x": "y"}, {"x": "bytes"})


# ---------------------------------------------------------------------------
# apply_normalizations
# ---------------------------------------------------------------------------

class TestApplyNormalizations:
    def test_chain_all_steps(self):
        records = [
            {"level": "  ERROR  ", "code": "200"},
        ]
        results = list(
            apply_normalizations(
                records,
                case_fields=["level"],
                case_mode="lower",
                strip_fields=["level"],
                type_map={"code": "int"},
            )
        )
        assert results == [{"level": "error", "code": 200}]

    def test_no_ops_passthrough(self):
        records = [{"a": "B"}]
        results = list(apply_normalizations(records))
        assert results == [{"a": "B"}]

    def test_empty_stream(self):
        assert list(apply_normalizations([])) == []
