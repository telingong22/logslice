"""Tests for logslice.cli_counter."""
import io
import json
import argparse
import pytest

from logslice.cli_counter import add_counter_args, run_counter


def _make_args(**kwargs):
    defaults = {"count": False, "count_by": None, "count_interval": None, "annotate_index": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stream(*lines):
    return io.StringIO("\n".join(lines) + "\n")


LINES = [
    '{"level":"info","time":1000}',
    '{"level":"warn","time":1045}',
    '{"level":"info","time":1090}',
    '{"level":"error","time":1200}',
]


class TestRunCounter:
    def test_count_returns_true(self, capsys):
        args = _make_args(count=True)
        result = run_counter(args, _stream(*LINES))
        assert result is True
        out = capsys.readouterr().out.strip()
        assert out == "4"

    def test_count_by_returns_true(self, capsys):
        args = _make_args(count_by="level")
        result = run_counter(args, _stream(*LINES))
        assert result is True
        out = capsys.readouterr().out.strip().splitlines()
        parsed = [json.loads(l) for l in out]
        counts = {r["level"]: r["count"] for r in parsed}
        assert counts["info"] == 2
        assert counts["warn"] == 1

    def test_count_interval_returns_true(self, capsys):
        args = _make_args(count_interval=60)
        result = run_counter(args, _stream(*LINES))
        assert result is True
        out = capsys.readouterr().out.strip().splitlines()
        assert len(out) >= 1
        first = json.loads(out[0])
        assert "bucket" in first and "count" in first

    def test_no_action_returns_false(self):
        args = _make_args()
        result = run_counter(args, _stream(*LINES))
        assert result is False

    def test_count_empty_stream(self, capsys):
        args = _make_args(count=True)
        result = run_counter(args, io.StringIO(""))
        assert result is True
        assert capsys.readouterr().out.strip() == "0"


class TestAddCounterArgs:
    def test_adds_count_flag(self):
        p = argparse.ArgumentParser()
        add_counter_args(p)
        ns = p.parse_args(["--count"])
        assert ns.count is True

    def test_adds_count_by(self):
        p = argparse.ArgumentParser()
        add_counter_args(p)
        ns = p.parse_args(["--count-by", "level"])
        assert ns.count_by == "level"

    def test_adds_count_interval(self):
        p = argparse.ArgumentParser()
        add_counter_args(p)
        ns = p.parse_args(["--count-interval", "30"])
        assert ns.count_interval == 30
