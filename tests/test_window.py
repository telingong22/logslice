"""Tests for logslice.window."""

import pytest
from logslice.window import tumbling_windows, window_summary


def _r(ts: str, value=None):
    r = {"timestamp": ts}
    if value is not None:
        r["value"] = value
    return r


class TestTumblingWindows:
    def test_single_window(self):
        records = [_r("2024-01-01T00:00:01Z"), _r("2024-01-01T00:00:02Z")]
        windows = list(tumbling_windows(records, interval_seconds=60))
        assert len(windows) == 1
        assert len(windows[0]) == 2

    def test_two_windows(self):
        records = [
            _r("2024-01-01T00:00:00Z"),
            _r("2024-01-01T00:01:01Z"),
        ]
        windows = list(tumbling_windows(records, interval_seconds=60))
        assert len(windows) == 2

    def test_empty_input(self):
        assert list(tumbling_windows([], interval_seconds=10)) == []

    def test_skips_records_without_timestamp(self):
        records = [{"msg": "no ts"}, _r("2024-01-01T00:00:01Z")]
        windows = list(tumbling_windows(records, interval_seconds=60))
        assert len(windows) == 1
        assert len(windows[0]) == 1

    def test_three_windows(self):
        records = [
            _r("2024-01-01T00:00:00Z"),
            _r("2024-01-01T00:01:00Z"),
            _r("2024-01-01T00:02:00Z"),
        ]
        windows = list(tumbling_windows(records, interval_seconds=59))
        assert len(windows) == 3


class TestWindowSummary:
    def test_count_only(self):
        window = [_r("2024-01-01T00:00:01Z"), _r("2024-01-01T00:00:02Z")]
        s = window_summary(window)
        assert s["count"] == 2
        assert "sum" not in s

    def test_with_numeric_field(self):
        window = [_r("2024-01-01T00:00:01Z", 10), _r("2024-01-01T00:00:02Z", 20)]
        s = window_summary(window, count_field="value")
        assert s["count"] == 2
        assert s["sum"] == 30
        assert s["min"] == 10
        assert s["max"] == 20
        assert s["avg"] == 15

    def test_skips_non_numeric(self):
        window = [_r("2024-01-01T00:00:01Z"), {"value": "bad", "timestamp": "2024-01-01T00:00:02Z"}]
        s = window_summary(window, count_field="value")
        assert s["count"] == 2
        assert "sum" not in s

    def test_empty_window(self):
        s = window_summary([])
        assert s["count"] == 0
