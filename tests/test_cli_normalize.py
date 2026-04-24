"""Tests for logslice.cli_normalize."""

import argparse
import io
import json

import pytest

from logslice.cli_normalize import _parse_coerce_specs, run_normalize


def _make_args(
    case=None,
    case_mode="lower",
    strip=None,
    strip_chars=None,
    coerce=None,
):
    ns = argparse.Namespace(
        case=case or [],
        case_mode=case_mode,
        strip=strip or [],
        strip_chars=strip_chars,
        coerce=coerce or [],
    )
    return ns


def _stream(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def _parsed_output(out: io.StringIO):
    out.seek(0)
    return [json.loads(line) for line in out if line.strip()]


# ---------------------------------------------------------------------------
# _parse_coerce_specs
# ---------------------------------------------------------------------------

class TestParseCoerceSpecs:
    def test_single(self):
        assert _parse_coerce_specs(["code:int"]) == {"code": "int"}

    def test_multiple(self):
        result = _parse_coerce_specs(["code:int", "latency:float"])
        assert result == {"code": "int", "latency": "float"}

    def test_empty(self):
        assert _parse_coerce_specs([]) == {}

    def test_invalid_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_coerce_specs(["badspec"])


# ---------------------------------------------------------------------------
# run_normalize
# ---------------------------------------------------------------------------

class TestRunNormalize:
    def test_returns_true(self):
        args = _make_args()
        result = run_normalize(args, stream=_stream({"a": "B"}), out=io.StringIO())
        assert result is True

    def test_case_lower(self):
        args = _make_args(case=["level"])
        out = io.StringIO()
        run_normalize(args, stream=_stream({"level": "ERROR"}), out=out)
        assert _parsed_output(out) == [{"level": "error"}]

    def test_case_upper(self):
        args = _make_args(case=["level"], case_mode="upper")
        out = io.StringIO()
        run_normalize(args, stream=_stream({"level": "info"}), out=out)
        assert _parsed_output(out) == [{"level": "INFO"}]

    def test_strip_whitespace(self):
        args = _make_args(strip=["msg"])
        out = io.StringIO()
        run_normalize(args, stream=_stream({"msg": "  hello  "}), out=out)
        assert _parsed_output(out) == [{"msg": "hello"}]

    def test_coerce_int(self):
        args = _make_args(coerce=["status:int"])
        out = io.StringIO()
        run_normalize(args, stream=_stream({"status": "200"}), out=out)
        assert _parsed_output(out) == [{"status": 200}]

    def test_invalid_json_lines_skipped(self):
        stream = io.StringIO("not json\n{\"a\": 1}\n")
        args = _make_args()
        out = io.StringIO()
        run_normalize(args, stream=stream, out=out)
        assert _parsed_output(out) == [{"a": 1}]

    def test_empty_stream(self):
        args = _make_args()
        out = io.StringIO()
        run_normalize(args, stream=io.StringIO(), out=out)
        assert _parsed_output(out) == []

    def test_chain_case_and_coerce(self):
        args = _make_args(case=["level"], coerce=["code:int"])
        out = io.StringIO()
        run_normalize(
            args,
            stream=_stream({"level": "WARN", "code": "503"}),
            out=out,
        )
        assert _parsed_output(out) == [{"level": "warn", "code": 503}]
