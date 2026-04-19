"""Tests for logslice.output module."""
import io
import json

import pytest

from logslice.output import (
    FORMAT_JSON,
    FORMAT_LOGFMT,
    FORMAT_PRETTY,
    format_record,
    write_records,
)

SAMPLE = {"level": "info", "msg": "hello world", "ts": "2024-01-01T00:00:00Z"}


class TestFormatRecord:
    def test_json_default(self):
        result = format_record(SAMPLE)
        parsed = json.loads(result)
        assert parsed == SAMPLE

    def test_json_explicit(self):
        result = format_record(SAMPLE, fmt=FORMAT_JSON)
        parsed = json.loads(result)
        assert parsed == SAMPLE

    def test_logfmt_simple(self):
        record = {"level": "info", "code": 200}
        result = format_record(record, fmt=FORMAT_LOGFMT)
        assert "level=info" in result
        assert "code=200" in result

    def test_logfmt_quotes_spaces(self):
        record = {"msg": "hello world"}
        result = format_record(record, fmt=FORMAT_LOGFMT)
        assert 'msg="hello world"' in result

    def test_pretty_format(self):
        record = {"level": "warn"}
        result = format_record(record, fmt=FORMAT_PRETTY)
        assert result.startswith("---")
        assert "level: warn" in result


class TestWriteRecords:
    def test_writes_all(self):
        out = io.StringIO()
        records = [{"a": 1}, {"a": 2}, {"a": 3}]
        count = write_records(records, out=out)
        assert count == 3
        lines = out.getvalue().strip().split("\n")
        assert len(lines) == 3

    def test_limit(self):
        out = io.StringIO()
        records = [{"a": i} for i in range(10)]
        count = write_records(records, out=out, limit=4)
        assert count == 4

    def test_limit_zero(self):
        out = io.StringIO()
        records = [{"a": i} for i in range(10)]
        count = write_records(records, out=out, limit=0)
        assert count == 0
        assert out.getvalue() == ""

    def test_empty(self):
        out = io.StringIO()
        count = write_records([], out=out)
        assert count == 0
        assert out.getvalue() == ""
