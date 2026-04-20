"""Integration tests: histogram module + CLI round-trip."""
import io
import json

from logslice.histogram import field_histogram, render_histogram
from logslice.cli_histogram import run_histogram
import argparse


def _args(**kw) -> argparse.Namespace:
    base = {"field": "status", "top": 10, "width": 40, "title": None, "json_out": False}
    base.update(kw)
    return argparse.Namespace(**base)


STATUS_LOGS = [
    '{"status": "200"}',
    '{"status": "200"}',
    '{"status": "404"}',
    '{"status": "500"}',
    '{"status": "200"}',
    '{"status": "404"}',
    '{"unrelated": "x"}',
]


def _stream() -> io.StringIO:
    return io.StringIO("\n".join(STATUS_LOGS) + "\n")


class TestHistogramIntegration:
    def test_field_histogram_matches_cli_json(self):
        """field_histogram and CLI --json-out should agree on counts."""
        from logslice.parser import parse_line

        records = [parse_line(l) for l in STATUS_LOGS]
        records = [r for r in records if r is not None]
        expected = dict(field_histogram(records, "status"))

        out = io.StringIO()
        run_histogram(_args(json_out=True), _stream(), out)
        cli_data = {item["value"]: item["count"] for item in json.loads(out.getvalue())}

        assert cli_data == expected

    def test_render_histogram_output_matches_cli_ascii(self):
        """Rendered ASCII from module and CLI should be identical."""
        from logslice.parser import parse_line

        records = [parse_line(l) for l in STATUS_LOGS]
        records = [r for r in records if r is not None]
        data = field_histogram(records, "status")
        expected_text = render_histogram(data, width=40, title="Histogram: status")

        out = io.StringIO()
        run_histogram(_args(), _stream(), out)
        cli_text = out.getvalue().rstrip("\n")

        assert cli_text == expected_text

    def test_top_respected_end_to_end(self):
        out = io.StringIO()
        run_histogram(_args(top=1, json_out=True), _stream(), out)
        data = json.loads(out.getvalue())
        assert len(data) == 1
        assert data[0]["value"] == "200"  # highest count

    def test_no_matching_field_empty_histogram(self):
        out = io.StringIO()
        run_histogram(_args(field="nonexistent", json_out=True), _stream(), out)
        data = json.loads(out.getvalue())
        assert data == []
