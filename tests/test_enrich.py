"""Tests for logslice.enrich."""

import pytest

from logslice.enrich import (
    apply_enrichments,
    enrich_computed,
    enrich_copy,
    enrich_regex,
    enrich_static,
)


# ---------------------------------------------------------------------------
# enrich_static
# ---------------------------------------------------------------------------

class TestEnrichStatic:
    def test_adds_field(self):
        records = [{"msg": "hello"}]
        result = list(enrich_static(records, "env", "prod"))
        assert result == [{"msg": "hello", "env": "prod"}]

    def test_overwrites_existing(self):
        records = [{"env": "dev"}]
        result = list(enrich_static(records, "env", "prod"))
        assert result[0]["env"] == "prod"

    def test_does_not_mutate_original(self):
        original = {"msg": "hi"}
        list(enrich_static([original], "env", "prod"))
        assert "env" not in original

    def test_empty_input(self):
        assert list(enrich_static([], "env", "prod")) == []


# ---------------------------------------------------------------------------
# enrich_copy
# ---------------------------------------------------------------------------

class TestEnrichCopy:
    def test_copies_field(self):
        records = [{"host": "web-1"}]
        result = list(enrich_copy(records, "host", "hostname"))
        assert result[0]["hostname"] == "web-1"
        assert result[0]["host"] == "web-1"

    def test_missing_src_skipped(self):
        records = [{"level": "info"}]
        result = list(enrich_copy(records, "host", "hostname"))
        assert "hostname" not in result[0]

    def test_does_not_mutate_original(self):
        original = {"host": "web-1"}
        list(enrich_copy([original], "host", "hostname"))
        assert "hostname" not in original


# ---------------------------------------------------------------------------
# enrich_regex
# ---------------------------------------------------------------------------

class TestEnrichRegex:
    def test_extracts_named_group(self):
        records = [{"msg": "status=200 path=/api"}]
        result = list(
            enrich_regex(records, "msg", r"status=(?P<code>\d+)", {"code": "status_code"})
        )
        assert result[0]["status_code"] == "200"

    def test_no_match_passes_through(self):
        records = [{"msg": "no match here"}]
        result = list(
            enrich_regex(records, "msg", r"status=(?P<code>\d+)", {"code": "status_code"})
        )
        assert "status_code" not in result[0]

    def test_missing_src_passes_through(self):
        records = [{"level": "info"}]
        result = list(
            enrich_regex(records, "msg", r"(?P<code>\d+)", {"code": "status_code"})
        )
        assert "status_code" not in result[0]

    def test_multiple_groups(self):
        records = [{"msg": "method=GET path=/health"}]
        result = list(
            enrich_regex(
                records,
                "msg",
                r"method=(?P<method>\w+) path=(?P<path>\S+)",
                {"method": "http_method", "path": "http_path"},
            )
        )
        assert result[0]["http_method"] == "GET"
        assert result[0]["http_path"] == "/health"


# ---------------------------------------------------------------------------
# enrich_computed
# ---------------------------------------------------------------------------

class TestEnrichComputed:
    def test_derives_field(self):
        records = [{"a": 3, "b": 4}]
        result = list(enrich_computed(records, "sum", lambda r: r["a"] + r["b"]))
        assert result[0]["sum"] == 7

    def test_exception_skips_field(self):
        records = [{"a": 1}]
        result = list(enrich_computed(records, "ratio", lambda r: r["a"] / r["b"]))
        assert "ratio" not in result[0]

    def test_does_not_mutate_original(self):
        original = {"x": 10}
        list(enrich_computed([original], "doubled", lambda r: r["x"] * 2))
        assert "doubled" not in original


# ---------------------------------------------------------------------------
# apply_enrichments
# ---------------------------------------------------------------------------

class TestApplyEnrichments:
    def test_static_step(self):
        records = [{"msg": "hi"}]
        steps = [{"type": "static", "field": "env", "value": "staging"}]
        result = list(apply_enrichments(records, steps))
        assert result[0]["env"] == "staging"

    def test_copy_step(self):
        records = [{"host": "srv-1"}]
        steps = [{"type": "copy", "src": "host", "dst": "server"}]
        result = list(apply_enrichments(records, steps))
        assert result[0]["server"] == "srv-1"

    def test_regex_step(self):
        records = [{"msg": "code=404"}]
        steps = [
            {
                "type": "regex",
                "src": "msg",
                "pattern": r"code=(?P<code>\d+)",
                "mappings": {"code": "status"},
            }
        ]
        result = list(apply_enrichments(records, steps))
        assert result[0]["status"] == "404"

    def test_chained_steps(self):
        records = [{"host": "web-1"}]
        steps = [
            {"type": "copy", "src": "host", "dst": "server"},
            {"type": "static", "field": "env", "value": "prod"},
        ]
        result = list(apply_enrichments(records, steps))
        assert result[0]["server"] == "web-1"
        assert result[0]["env"] == "prod"

    def test_unknown_type_raises(self):
        records = [{"msg": "hi"}]
        steps = [{"type": "unknown_op", "field": "x"}]
        with pytest.raises(ValueError, match="Unknown enrichment type"):
            list(apply_enrichments(records, steps))
