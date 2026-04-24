"""Unit tests for logslice.cli_resample."""

import io
import json
import types

import pytest
from logslice.cli_resample import run_resample, _read_records


def _make_args(**kwargs):
    defaults = {
        "interval": 60,
        "ts_field": "timestamp",
        "agg": "count",
        "value_field": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _stream(*lines):
    return io.StringIO("\n".join(lines) + "\n")


def _parsed_output(out: io.StringIO):
    out.seek(0)
    return [json.loads(line) for line in out if line.strip()]


class TestRunResample:
    def test_returns_true_on_success(self):
        stream = _stream(json.dumps({"timestamp": "2024-01-01T12:00:10Z"}))
        out = io.StringIO()
        assert run_resample(_make_args(), stream=stream, out=out) is True

    def test_empty_input_returns_true(self):
        out = io.StringIO()
        assert run_resample(_make_args(), stream=io.StringIO(), out=out) is True
        assert _parsed_output(out) == []

    def test_count_single_bucket(self):
        lines = [
            json.dumps({"timestamp": "2024-01-01T12:00:10Z"}),
            json.dumps({"timestamp": "2024-01-01T12:00:50Z"}),
        ]
        out = io.StringIO()
        run_resample(_make_args(), stream=_stream(*lines), out=out)
        results = _parsed_output(out)
        assert len(results) == 1
        assert results[0]["count"] == 2

    def test_count_two_buckets(self):
        lines = [
            json.dumps({"timestamp": "2024-01-01T12:00:10Z"}),
            json.dumps({"timestamp": "2024-01-01T12:01:10Z"}),
        ]
        out = io.StringIO()
        run_resample(_make_args(), stream=_stream(*lines), out=out)
        results = _parsed_output(out)
        assert len(results) == 2

    def test_sum_aggregation(self):
        lines = [
            json.dumps({"timestamp": "2024-01-01T12:00:10Z", "val": 4}),
            json.dumps({"timestamp": "2024-01-01T12:00:20Z", "val": 6}),
        ]
        out = io.StringIO()
        run_resample(_make_args(agg="sum", value_field="val"), stream=_stream(*lines), out=out)
        results = _parsed_output(out)
        assert results[0]["sum"] == 10.0

    def test_invalid_interval_returns_false(self):
        out = io.StringIO()
        result = run_resample(_make_args(interval=-1), stream=io.StringIO(), out=out)
        assert result is False

    def test_missing_value_field_returns_false(self):
        out = io.StringIO()
        result = run_resample(_make_args(agg="sum", value_field=None), stream=io.StringIO(), out=out)
        assert result is False

    def test_custom_ts_field(self):
        lines = [json.dumps({"ts": "2024-01-01T12:00:10Z"})]
        out = io.StringIO()
        run_resample(_make_args(ts_field="ts"), stream=_stream(*lines), out=out)
        results = _parsed_output(out)
        assert len(results) == 1

    def test_invalid_json_lines_skipped(self):
        lines = ["not json", json.dumps({"timestamp": "2024-01-01T12:00:10Z"})]
        out = io.StringIO()
        run_resample(_make_args(), stream=_stream(*lines), out=out)
        results = _parsed_output(out)
        assert len(results) == 1
