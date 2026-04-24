"""Tests for logslice.cli_enrich."""

import argparse
import json
import pytest

from logslice.cli_enrich import _parse_step, add_enrich_args, run_enrich


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"steps": [], "output_format": "json"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stream(*records):
    return [json.dumps(r) for r in records]


def _parsed_output(capsys):
    out = capsys.readouterr().out
    return [json.loads(line) for line in out.strip().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# _parse_step
# ---------------------------------------------------------------------------

class TestParseStep:
    def test_static_shortcut(self):
        step = _parse_step("static:env=prod")
        assert step == {"type": "static", "field": "env", "value": "prod"}

    def test_copy_shortcut(self):
        step = _parse_step("copy:host->hostname")
        assert step == {"type": "copy", "src": "host", "dst": "hostname"}

    def test_json_step(self):
        raw = json.dumps({"type": "static", "field": "x", "value": "1"})
        step = _parse_step(raw)
        assert step["type"] == "static"

    def test_invalid_json_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_step("{not valid json")

    def test_invalid_static_spec_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_step("static:")

    def test_invalid_copy_spec_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_step("copy:onlysrc")


# ---------------------------------------------------------------------------
# add_enrich_args
# ---------------------------------------------------------------------------

class TestAddEnrichArgs:
    def test_defaults(self):
        parser = argparse.ArgumentParser()
        add_enrich_args(parser)
        args = parser.parse_args([])
        assert args.steps == []
        assert args.output_format == "json"

    def test_multiple_steps(self):
        parser = argparse.ArgumentParser()
        add_enrich_args(parser)
        args = parser.parse_args(["--step", "static:env=prod", "--step", "copy:host->server"])
        assert len(args.steps) == 2


# ---------------------------------------------------------------------------
# run_enrich
# ---------------------------------------------------------------------------

class TestRunEnrich:
    def test_static_enrichment(self, capsys):
        lines = _stream({"msg": "hello"}, {"msg": "world"})
        args = _make_args(steps=["static:env=prod"])
        result = run_enrich(args, lines)
        assert result is True
        records = _parsed_output(capsys)
        assert all(r["env"] == "prod" for r in records)

    def test_copy_enrichment(self, capsys):
        lines = _stream({"host": "web-1"})
        args = _make_args(steps=["copy:host->server"])
        run_enrich(args, lines)
        records = _parsed_output(capsys)
        assert records[0]["server"] == "web-1"
        assert records[0]["host"] == "web-1"

    def test_no_steps_passthrough(self, capsys):
        lines = _stream({"msg": "hi"}, {"msg": "bye"})
        args = _make_args()
        run_enrich(args, lines)
        records = _parsed_output(capsys)
        assert len(records) == 2

    def test_invalid_json_lines_skipped(self, capsys):
        lines = ["not json", json.dumps({"msg": "ok"})]
        args = _make_args(steps=["static:env=test"])
        run_enrich(args, lines)
        records = _parsed_output(capsys)
        assert len(records) == 1
        assert records[0]["env"] == "test"

    def test_chained_steps(self, capsys):
        lines = _stream({"host": "srv-1"})
        args = _make_args(steps=["copy:host->server", "static:env=staging"])
        run_enrich(args, lines)
        records = _parsed_output(capsys)
        assert records[0]["server"] == "srv-1"
        assert records[0]["env"] == "staging"

    def test_logfmt_output_format(self, capsys):
        lines = _stream({"msg": "hello"})
        args = _make_args(steps=["static:env=prod"], output_format="logfmt")
        run_enrich(args, lines)
        out = capsys.readouterr().out
        assert "env=prod" in out
