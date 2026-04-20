"""Tests for logslice.histogram."""
import pytest

from logslice.histogram import (
    field_histogram,
    render_bar,
    render_histogram,
    histogram_records,
)


RECORDS = [
    {"level": "info"},
    {"level": "info"},
    {"level": "warn"},
    {"level": "error"},
    {"level": "info"},
    {"level": "warn"},
    {"other": "x"},  # missing 'level'
]


class TestFieldHistogram:
    def test_counts_correctly(self):
        data = field_histogram(RECORDS, "level")
        counts = dict(data)
        assert counts["info"] == 3
        assert counts["warn"] == 2
        assert counts["error"] == 1

    def test_missing_field_ignored(self):
        data = field_histogram(RECORDS, "level")
        labels = [label for label, _ in data]
        assert "None" not in labels

    def test_top_n_limits_results(self):
        data = field_histogram(RECORDS, "level", top=2)
        assert len(data) == 2

    def test_sorted_descending(self):
        data = field_histogram(RECORDS, "level")
        counts = [c for _, c in data]
        assert counts == sorted(counts, reverse=True)

    def test_empty_input(self):
        data = field_histogram([], "level")
        assert data == []

    def test_missing_field_all_records(self):
        data = field_histogram([{"x": 1}], "level")
        assert data == []


class TestRenderBar:
    def test_full_bar(self):
        bar = render_bar("info", 10, 10, width=10)
        assert "██████████" in bar

    def test_half_bar(self):
        bar = render_bar("warn", 5, 10, width=10)
        assert "█████" in bar
        assert bar.count("█") == 5

    def test_zero_max_count(self):
        bar = render_bar("x", 0, 0, width=10)
        assert "0" in bar

    def test_label_in_output(self):
        bar = render_bar("my_label", 3, 10)
        assert "my_label" in bar

    def test_count_in_output(self):
        bar = render_bar("x", 7, 10)
        assert "7" in bar


class TestRenderHistogram:
    def test_empty_data_returns_no_data(self):
        result = render_histogram([])
        assert result == "(no data)"

    def test_title_included(self):
        result = render_histogram([("info", 3)], title="My Title")
        assert "My Title" in result

    def test_all_labels_present(self):
        data = [("info", 3), ("warn", 2)]
        result = render_histogram(data)
        assert "info" in result
        assert "warn" in result

    def test_no_title_no_header_line(self):
        result = render_histogram([("x", 1)], title=None)
        assert "---" not in result


class TestHistogramRecords:
    def test_returns_string(self):
        result = histogram_records(RECORDS, "level")
        assert isinstance(result, str)

    def test_default_title_contains_field(self):
        result = histogram_records(RECORDS, "level")
        assert "level" in result

    def test_custom_title(self):
        result = histogram_records(RECORDS, "level", title="Custom")
        assert "Custom" in result
