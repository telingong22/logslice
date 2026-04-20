"""Tests for logslice.cli_histogram."""
import argparse
import io
import json

import pytest

from logslice.cli_histogram import add_histogram_args, run_histogram


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "field": "level",
        "top": 10,
        "width": 40,
        "title": None,
        "json_out": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stream(*lines: str) -> io.StringIO:
    return io.StringIO("\n".join(lines) + "\n")


LOG_LINES = [
    '{"level": "info", "msg": "started"}',
    '{"level": "info", "msg": "running"}',
    '{"level": "warn", "msg": "slow"}',
    '{"level": "error", "msg": "failed"}',
    '{"level": "info", "msg": "done"}',
]


class TestRunHistogram:
    def test_returns_true(self):
        out = io.StringIO()
        result = run_histogram(_make_args(), _stream(*LOG_LINES), out)
        assert result is True

    def test_ascii_output_contains_field_values(self):
        out = io.StringIO()
        run_histogram(_make_args(field="level"), _stream(*LOG_LINES), out)
        text = out.getvalue()
        assert "info" in text
        assert "warn" in text
        assert "error" in text

    def test_default_title_in_output(self):
        out = io.StringIO()
        run_histogram(_make_args(field="level"), _stream(*LOG_LINES), out)
        assert "level" in out.getvalue()

    def test_custom_title(self):
        out = io.StringIO()
        run_histogram(
            _make_args(field="level", title="MyTitle"),
            _stream(*LOG_LINES),
            out,
        )
        assert "MyTitle" in out.getvalue()

    def test_json_out_is_valid_json(self):
        out = io.StringIO()
        run_histogram(
            _make_args(field="level", json_out=True),
            _stream(*LOG_LINES),
            out,
        )
        data = json.loads(out.getvalue())
        assert isinstance(data, list)
        assert all("value" in item and "count" in item for item in data)

    def test_json_out_counts_correct(self):
        out = io.StringIO()
        run_histogram(
            _make_args(field="level", json_out=True),
            _stream(*LOG_LINES),
            out,
        )
        data = {item["value"]: item["count"] for item in json.loads(out.getvalue())}
        assert data["info"] == 3
        assert data["warn"] == 1
        assert data["error"] == 1

    def test_top_n_limits_json_output(self):
        out = io.StringIO()
        run_histogram(
            _make_args(field="level", top=2, json_out=True),
            _stream(*LOG_LINES),
            out,
        )
        data = json.loads(out.getvalue())
        assert len(data) == 2

    def test_empty_input(self):
        out = io.StringIO()
        result = run_histogram(_make_args(), io.StringIO(""), out)
        assert result is True

    def test_add_histogram_args_registers_subcommand(self):
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        add_histogram_args(subs)
        args = parser.parse_args(["histogram", "level"])
        assert args.field == "level"
        assert args.top == 10
