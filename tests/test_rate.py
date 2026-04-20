"""Tests for logslice.rate and logslice.cli_rate."""

from __future__ import annotations

import argparse
import io
import json

import pytest

from logslice.rate import compute_rate, rate_records
from logslice.cli_rate import add_rate_args, run_rate


def _r(ts: float) -> dict:
    return {"timestamp": ts, "msg": "event"}


# ---------------------------------------------------------------------------
# compute_rate
# ---------------------------------------------------------------------------

class TestComputeRate:
    def test_empty_input_returns_empty(self):
        assert compute_rate([]) == []

    def test_single_event_one_bucket(self):
        result = compute_rate([_r(0.0)], interval_seconds=60.0)
        assert len(result) == 1
        assert result[0]["count"] == 1
        assert result[0]["bucket"] == 0.0

    def test_two_events_same_bucket(self):
        result = compute_rate([_r(10.0), _r(50.0)], interval_seconds=60.0)
        assert len(result) == 1
        assert result[0]["count"] == 2

    def test_events_in_different_buckets(self):
        result = compute_rate([_r(0.0), _r(60.0), _r(120.0)], interval_seconds=60.0)
        assert len(result) == 3
        counts = [r["count"] for r in result]
        assert counts == [1, 1, 1]

    def test_rate_per_sec_correct(self):
        result = compute_rate([_r(0.0), _r(10.0)], interval_seconds=60.0)
        assert result[0]["rate_per_sec"] == round(2 / 60.0, 6)

    def test_records_without_timestamp_ignored(self):
        records = [{"msg": "no ts"}, _r(0.0)]
        result = compute_rate(records, interval_seconds=60.0)
        assert len(result) == 1
        assert result[0]["count"] == 1

    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError):
            compute_rate([_r(0.0)], interval_seconds=0)

    def test_custom_ts_field(self):
        records = [{"t": 0.0}, {"t": 30.0}]
        result = compute_rate(records, interval_seconds=60.0, ts_field="t")
        assert result[0]["count"] == 2

    def test_buckets_sorted_ascending(self):
        result = compute_rate([_r(120.0), _r(0.0), _r(60.0)], interval_seconds=60.0)
        buckets = [r["bucket"] for r in result]
        assert buckets == sorted(buckets)

    def test_rate_records_yields_same(self):
        records = [_r(0.0), _r(10.0)]
        assert list(rate_records(records, interval_seconds=60.0)) == compute_rate(
            records, interval_seconds=60.0
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"interval": 60.0, "ts_field": "timestamp", "format": "json", "func": run_rate}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stream(records):
    return io.StringIO("\n".join(json.dumps(r) for r in records))


class TestRunRate:
    def test_returns_true(self, capsys):
        result = run_rate(_make_args(), _stream([_r(0.0)]))
        assert result is True

    def test_json_output_parseable(self, capsys):
        run_rate(_make_args(), _stream([_r(0.0), _r(30.0)]))
        out = capsys.readouterr().out.strip()
        row = json.loads(out)
        assert row["count"] == 2

    def test_text_output_contains_count(self, capsys):
        run_rate(_make_args(format="text"), _stream([_r(0.0)]))
        out = capsys.readouterr().out
        assert "count=1" in out

    def test_empty_stream_no_output(self, capsys):
        run_rate(_make_args(), _stream([]))
        assert capsys.readouterr().out.strip() == ""

    def test_add_rate_args_registers_subcommand(self):
        p = argparse.ArgumentParser()
        subs = p.add_subparsers()
        add_rate_args(subs)
        args = p.parse_args(["rate", "--interval", "30"])
        assert args.interval == 30.0
