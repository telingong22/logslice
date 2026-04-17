"""Tests for logslice.parser module."""

import pytest
from logslice.parser import parse_line


class TestJsonParsing:
    def test_valid_json_line(self):
        line = '{"level": "info", "msg": "started", "ts": "2024-01-01T00:00:00Z"}'
        result = parse_line(line)
        assert result == {"level": "info", "msg": "started", "ts": "2024-01-01T00:00:00Z"}

    def test_invalid_json_falls_through(self):
        line = '{bad json'
        result = parse_line(line)
        assert result is None

    def test_empty_json_object(self):
        result = parse_line("{}")
        assert result == {}


class TestLogfmtParsing:
    def test_simple_logfmt(self):
        line = "level=info msg=started"
        result = parse_line(line)
        assert result == {"level": "info", "msg": "started"}

    def test_quoted_values(self):
        line = 'level=info msg="server started" port=8080'
        result = parse_line(line)
        assert result == {"level": "info", "msg": "server started", "port": "8080"}

    def test_single_pair(self):
        result = parse_line("key=value")
        assert result == {"key": "value"}

    def test_logfmt_with_timestamp(self):
        line = "ts=2024-01-01T00:00:00Z level=error msg=failed"
        result = parse_line(line)
        assert result["ts"] == "2024-01-01T00:00:00Z"
        assert result["level"] == "error"


class TestEdgeCases:
    def test_empty_line(self):
        assert parse_line("") is None

    def test_whitespace_only(self):
        assert parse_line("   ") is None

    def test_strips_newline(self):
        line = '{"a": 1}\n'
        result = parse_line(line)
        assert result == {"a": 1}
