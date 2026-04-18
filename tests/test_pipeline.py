"""Integration tests for logslice.pipeline."""

import json
import pytest
from logslice.pipeline import run_pipeline, run_pipeline_transformed


def _lines(*records):
    return [json.dumps(r) for r in records]


RECORDS = [
    {"ts": "2024-06-01T10:00:00Z", "level": "info", "msg": "start", "user": "alice"},
    {"ts": "2024-06-01T11:00:00Z", "level": "error", "msg": "boom", "user": "bob"},
    {"ts": "2024-06-01T12:00:00Z", "level": "info", "msg": "end", "user": "alice"},
]


class TestRunPipeline:
    def test_no_filters_returns_all(self):
        result = list(run_pipeline(_lines(*RECORDS)))
        assert len(result) == 3

    def test_time_start_filter(self):
        result = list(run_pipeline(_lines(*RECORDS), start="2024-06-01T11:00:00Z"))
        assert len(result) == 2
        assert all(r["ts"] >= "2024-06-01T11:00:00Z" for r in result)

    def test_time_end_filter(self):
        result = list(run_pipeline(_lines(*RECORDS), end="2024-06-01T10:30:00Z"))
        assert len(result) == 1
        assert result[0]["msg"] == "start"

    def test_pattern_filter(self):
        result = list(run_pipeline(_lines(*RECORDS), patterns=["level=error"]))
        assert len(result) == 1
        assert result[0]["level"] == "error"

    def test_multiple_patterns_and(self):
        result = list(run_pipeline(_lines(*RECORDS), patterns=["level=info", "user=alice"]))
        assert len(result) == 2

    def test_skips_invalid_lines(self):
        lines = ["not json at all", json.dumps(RECORDS[0])]
        result = list(run_pipeline(lines))
        assert len(result) == 1

    def test_skips_empty_lines(self):
        lines = ["", "  ", json.dumps(RECORDS[0])]
        # empty/whitespace stripped lines should be skipped
        result = list(run_pipeline(lines))
        assert len(result) == 1


class TestRunPipelineTransformed:
    def test_rename_applied(self):
        result = list(
            run_pipeline_transformed(_lines(*RECORDS), renames={"msg": "message"})
        )
        assert all("message" in r for r in result)
        assert all("msg" not in r for r in result)

    def test_drop_applied(self):
        result = list(run_pipeline_transformed(_lines(*RECORDS), drop=["user"]))
        assert all("user" not in r for r in result)

    def test_keep_applied(self):
        result = list(run_pipeline_transformed(_lines(*RECORDS), keep=["level", "msg"]))
        assert all(set(r.keys()) == {"level", "msg"} for r in result)

    def test_filter_then_transform(self):
        result = list(
            run_pipeline_transformed(
                _lines(*RECORDS),
                patterns=["level=error"],
                drop=["user"],
            )
        )
        assert len(result) == 1
        assert "user" not in result[0]
