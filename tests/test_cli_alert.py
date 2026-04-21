"""Tests for logslice.cli_alert."""
import argparse
import io
import json
import pytest

from logslice.cli_alert import add_alert_args, run_alert, _parse_rule


def _make_args(**kwargs):
    defaults = dict(rules=[], match_any=False, annotate=False, label="_alert")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stream(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def _parsed_output(out_str):
    return [json.loads(line) for line in out_str.strip().splitlines()]


class TestParseRule:
    def test_valid_rule(self):
        assert _parse_rule("latency:gt:100") == ("latency", "gt", 100.0)

    def test_float_threshold(self):
        assert _parse_rule("score:lte:0.5") == ("score", "lte", 0.5)

    def test_bad_format_raises(self):
        with pytest.raises(argparse.ArgumentTypeError, match="Rule must be"):
            _parse_rule("latency-gt-100")

    def test_non_numeric_threshold_raises(self):
        with pytest.raises(argparse.ArgumentTypeError, match="numeric"):
            _parse_rule("latency:gt:high")


class TestRunAlert:
    def test_filter_by_single_rule(self):
        rules = [_parse_rule("latency:gt:100")]
        args = _make_args(rules=rules)
        stream = _stream({"latency": 50}, {"latency": 150})
        out = io.StringIO()
        run_alert(args, stream=stream, out=out)
        result = _parsed_output(out.getvalue())
        assert len(result) == 1
        assert result[0]["latency"] == 150

    def test_match_any_flag(self):
        rules = [_parse_rule("latency:gt:100"), _parse_rule("errors:gt:0")]
        args = _make_args(rules=rules, match_any=True)
        stream = _stream({"latency": 150, "errors": 0}, {"latency": 50, "errors": 3})
        out = io.StringIO()
        run_alert(args, stream=stream, out=out)
        result = _parsed_output(out.getvalue())
        assert len(result) == 2

    def test_annotate_mode(self):
        rules = [_parse_rule("latency:gt:100")]
        args = _make_args(rules=rules, annotate=True)
        stream = _stream({"latency": 50}, {"latency": 200})
        out = io.StringIO()
        run_alert(args, stream=stream, out=out)
        result = _parsed_output(out.getvalue())
        assert len(result) == 2
        assert result[0]["_alert"] is False
        assert result[1]["_alert"] is True

    def test_annotate_custom_label(self):
        rules = [_parse_rule("x:gt:0")]
        args = _make_args(rules=rules, annotate=True, label="fired")
        stream = _stream({"x": 1})
        out = io.StringIO()
        run_alert(args, stream=stream, out=out)
        result = _parsed_output(out.getvalue())
        assert "fired" in result[0]

    def test_empty_input(self):
        args = _make_args(rules=[_parse_rule("x:gt:0")])
        out = io.StringIO()
        run_alert(args, stream=io.StringIO(), out=out)
        assert out.getvalue() == ""

    def test_returns_true(self):
        args = _make_args()
        assert run_alert(args, stream=io.StringIO(), out=io.StringIO()) is True

    def test_add_alert_args_registers_rule(self):
        parser = argparse.ArgumentParser()
        add_alert_args(parser)
        args = parser.parse_args(["--rule", "latency:gt:100"])
        assert args.rules == [("latency", "gt", 100.0)]
