"""Tests for logslice.cli_score."""
import argparse
import io
import json
import pytest

from logslice.cli_score import _parse_rule, add_score_args, run_score


def _make_args(**kw):
    defaults = dict(rules=[], base=0.0, score_field="_score", min_score=None, top=None)
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def _stream(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records))


def _parsed_output(out: io.StringIO):
    return [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# _parse_rule
# ---------------------------------------------------------------------------

class TestParseRule:
    def test_string_value(self):
        field, value, weight = _parse_rule("level=error:5")
        assert field == "level"
        assert value == "error"
        assert weight == 5.0

    def test_integer_value_coerced(self):
        field, value, weight = _parse_rule("code=200:3.5")
        assert value == 200
        assert weight == 3.5

    def test_float_value_coerced(self):
        field, value, weight = _parse_rule("ratio=0.5:1")
        assert value == 0.5

    def test_invalid_spec_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_rule("badspec")

    def test_missing_weight_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_rule("level=error")


# ---------------------------------------------------------------------------
# run_score
# ---------------------------------------------------------------------------

class TestRunScore:
    def test_returns_true_on_success(self):
        args = _make_args()
        out = io.StringIO()
        assert run_score(args, stream=_stream({"level": "info"}), out=out) is True

    def test_score_annotated(self):
        rules = [_parse_rule("level=error:10")]
        args = _make_args(rules=rules)
        out = io.StringIO()
        run_score(args, stream=_stream({"level": "error"}), out=out)
        results = _parsed_output(out)
        assert results[0]["_score"] == 10.0

    def test_min_score_filters(self):
        rules = [_parse_rule("level=error:10")]
        args = _make_args(rules=rules, min_score=5.0)
        out = io.StringIO()
        run_score(
            args,
            stream=_stream({"level": "error"}, {"level": "info"}),
            out=out,
        )
        results = _parsed_output(out)
        assert len(results) == 1
        assert results[0]["level"] == "error"

    def test_top_n_limits_output(self):
        rules = [_parse_rule("level=error:10"), _parse_rule("service=auth:5")]
        args = _make_args(rules=rules, top=1)
        records = [
            {"level": "error", "service": "auth"},
            {"level": "error", "service": "web"},
            {"level": "info"},
        ]
        out = io.StringIO()
        run_score(args, stream=_stream(*records), out=out)
        results = _parsed_output(out)
        assert len(results) == 1
        assert results[0]["_score"] == 15.0

    def test_custom_score_field(self):
        args = _make_args(score_field="relevance")
        out = io.StringIO()
        run_score(args, stream=_stream({"x": 1}), out=out)
        results = _parsed_output(out)
        assert "relevance" in results[0]

    def test_base_score_applied(self):
        args = _make_args(base=3.0)
        out = io.StringIO()
        run_score(args, stream=_stream({"x": 1}), out=out)
        results = _parsed_output(out)
        assert results[0]["_score"] == 3.0

    def test_invalid_json_lines_skipped(self):
        stream = io.StringIO("not json\n{\"level\": \"info\"}\n")
        args = _make_args()
        out = io.StringIO()
        run_score(args, stream=stream, out=out)
        results = _parsed_output(out)
        assert len(results) == 1

    def test_empty_input(self):
        args = _make_args()
        out = io.StringIO()
        run_score(args, stream=io.StringIO(), out=out)
        assert out.getvalue() == ""
