"""Tests for logslice.partition and logslice.cli_partition."""

import argparse
import io
import json

import pytest

from logslice.partition import (
    iter_partitions,
    partition_by_rules,
    partition_by_value,
    partition_records,
)
from logslice.cli_partition import run_partition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _r(**kwargs):
    return dict(**kwargs)


def _make_args(field="level", default_bucket="__other__", summary=False):
    ns = argparse.Namespace(field=field, default_bucket=default_bucket, summary=summary)
    return ns


# ---------------------------------------------------------------------------
# partition_by_value
# ---------------------------------------------------------------------------

class TestPartitionByValue:
    def test_basic_split(self):
        records = [_r(level="info"), _r(level="error"), _r(level="info")]
        result = partition_by_value(records, "level")
        assert len(result["info"]) == 2
        assert len(result["error"]) == 1

    def test_missing_field_goes_to_default(self):
        records = [_r(msg="hi"), _r(level="warn")]
        result = partition_by_value(records, "level", default_bucket="unknown")
        assert "unknown" in result
        assert len(result["unknown"]) == 1

    def test_nested_field(self):
        records = [_r(meta={"env": "prod"}), _r(meta={"env": "dev"})]
        result = partition_by_value(records, "meta.env")
        assert "prod" in result
        assert "dev" in result

    def test_empty_input(self):
        assert partition_by_value([], "level") == {}


# ---------------------------------------------------------------------------
# partition_by_rules
# ---------------------------------------------------------------------------

class TestPartitionByRules:
    def test_first_match_wins(self):
        rules = [
            ("high", lambda r: r.get("status", 0) >= 500),
            ("low", lambda r: r.get("status", 0) >= 200),
        ]
        records = [_r(status=500), _r(status=200), _r(status=404)]
        result = partition_by_rules(records, rules)
        assert len(result["high"]) == 1
        assert len(result["low"]) == 2

    def test_no_match_uses_default(self):
        rules = [("ok", lambda r: r.get("status") == 200)]
        records = [_r(status=500)]
        result = partition_by_rules(records, rules, default_bucket="other")
        assert len(result["other"]) == 1

    def test_predicate_exception_skips(self):
        rules = [("boom", lambda r: r["missing_key"])]
        records = [_r(x=1)]
        result = partition_by_rules(records, rules, default_bucket="safe")
        assert len(result["safe"]) == 1


# ---------------------------------------------------------------------------
# partition_records
# ---------------------------------------------------------------------------

class TestPartitionRecords:
    def test_raises_without_field_or_rules(self):
        with pytest.raises(ValueError):
            partition_records([_r(a=1)])

    def test_rules_take_precedence_over_field(self):
        rules = [("x", lambda r: True)]
        result = partition_records([_r(level="info")], field="level", rules=rules)
        assert "x" in result


# ---------------------------------------------------------------------------
# iter_partitions
# ---------------------------------------------------------------------------

def test_iter_partitions_sorted():
    buckets = {"z": [_r(a=1)], "a": [_r(b=2)], "m": [_r(c=3)]}
    names = [name for name, _ in iter_partitions(buckets)]
    assert names == ["a", "m", "z"]


# ---------------------------------------------------------------------------
# CLI run_partition
# ---------------------------------------------------------------------------

class TestRunPartition:
    def _stream(self, records):
        return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")

    def _output(self, out_buf):
        out_buf.seek(0)
        return [json.loads(l) for l in out_buf if l.strip()]

    def test_returns_true_on_success(self):
        stream = self._stream([_r(level="info")])
        out = io.StringIO()
        assert run_partition(_make_args(), stream=stream, out=out) is True

    def test_no_field_returns_false(self):
        stream = self._stream([])
        out = io.StringIO()
        args = _make_args(field="")
        assert run_partition(args, stream=stream, out=out) is False

    def test_records_annotated_with_bucket(self):
        records = [_r(level="info"), _r(level="error")]
        stream = self._stream(records)
        out = io.StringIO()
        run_partition(_make_args(field="level"), stream=stream, out=out)
        parsed = self._output(out)
        assert all("_bucket" in r for r in parsed)

    def test_summary_mode(self):
        records = [_r(level="info")] * 3 + [_r(level="error")]
        stream = self._stream(records)
        out = io.StringIO()
        run_partition(_make_args(field="level", summary=True), stream=stream, out=out)
        parsed = self._output(out)
        counts = {r["bucket"]: r["count"] for r in parsed}
        assert counts["info"] == 3
        assert counts["error"] == 1

    def test_default_bucket_for_missing_field(self):
        records = [_r(msg="no level here")]
        stream = self._stream(records)
        out = io.StringIO()
        run_partition(
            _make_args(field="level", default_bucket="unknown", summary=True),
            stream=stream,
            out=out,
        )
        parsed = self._output(out)
        assert parsed[0]["bucket"] == "unknown"
