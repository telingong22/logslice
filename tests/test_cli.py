"""Tests for logslice CLI."""
import io
import json
from unittest.mock import patch

import pytest

from logslice.cli import run


JSON_LINES = """\n{"ts":"2024-01-01T10:00:00Z","level":"info","msg":"start"}
{"ts":"2024-01-01T11:00:00Z","level":"error","msg":"oops"}
{"ts":"2024-01-01T12:00:00Z","level":"info","msg":"end"}
"""


def _run_with_stdin(args, stdin_data):
    with patch("sys.stdin", io.StringIO(stdin_data)):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = run(args)
            return code, mock_out.getvalue()


def _parsed_lines(out):
    """Return a list of parsed JSON objects from CLI output, skipping blank lines."""
    return [json.loads(l) for l in out.strip().split("\n") if l]


class TestCLI:
    def test_no_filters_returns_all(self):
        code, out = _run_with_stdin([], JSON_LINES)
        assert code == 0
        assert len(_parsed_lines(out)) == 3

    def test_match_filter(self):
        code, out = _run_with_stdin(["--match", "level=error"], JSON_LINES)
        assert code == 0
        lines = _parsed_lines(out)
        assert len(lines) == 1
        assert lines[0]["level"] == "error"

    def test_time_range_filter(self):
        code, out = _run_with_stdin(
            ["--from", "2024-01-01T10:30:00Z", "--to", "2024-01-01T11:30:00Z"],
            JSON_LINES,
        )
        assert code == 0
        lines = _parsed_lines(out)
        assert len(lines) == 1
        assert lines[0]["level"] == "error"

    def test_limit(self):
        code, out = _run_with_stdin(["--limit", "1"], JSON_LINES)
        assert code == 0
        assert len(_parsed_lines(out)) == 1

    def test_invalid_match_returns_2(self):
        code, _ = _run_with_stdin(["--match", "badvalue"], JSON_LINES)
        assert code == 2

    def test_logfmt_output(self):
        code, out = _run_with_stdin(["--format", "logfmt", "--match", "level=info"], JSON_LINES)
        assert code == 0
        assert "level=info" in out
