"""Tests for logslice.highlight."""
import re

import pytest

from logslice.highlight import ANSI, highlight_keys, highlight_pattern, highlight_record


RESET = ANSI["reset"]


class TestHighlightKeys:
    def test_highlighted_key_contains_ansi(self):
        record = {"level": "info", "msg": "hello"}
        result = highlight_keys(record, keys=["level"])
        assert ANSI["cyan"] in result
        assert "level" in result

    def test_non_highlighted_key_plain(self):
        record = {"level": "info", "msg": "hello"}
        result = highlight_keys(record, keys=["level"])
        # 'msg' should appear without leading ANSI code
        assert f"{ANSI['cyan']}msg" not in result

    def test_empty_keys(self):
        record = {"a": 1, "b": 2}
        result = highlight_keys(record, keys=[])
        assert ANSI["cyan"] not in result

    def test_all_keys_highlighted(self):
        record = {"x": 1, "y": 2}
        result = highlight_keys(record, keys=["x", "y"])
        assert result.count(ANSI["cyan"]) == 2


class TestHighlightPattern:
    def test_match_wrapped(self):
        result = highlight_pattern("hello world", "world")
        assert ANSI["yellow"] in result
        assert "world" in result

    def test_no_match_unchanged(self):
        result = highlight_pattern("hello world", "xyz")
        assert result == "hello world"

    def test_ignore_case(self):
        result = highlight_pattern("Hello World", "hello", ignore_case=True)
        assert ANSI["yellow"] in result

    def test_invalid_regex_returns_original(self):
        text = "some [broken text"
        result = highlight_pattern(text, "[broken")
        assert result == text

    def test_multiple_occurrences(self):
        result = highlight_pattern("aa bb aa", "aa")
        assert result.count(ANSI["yellow"]) == 2


class TestHighlightRecord:
    def test_pattern_applied_to_values(self):
        record = {"msg": "error occurred", "level": "error"}
        result = highlight_record(record, pattern="error")
        assert ANSI["yellow"] in result

    def test_keys_and_pattern_combined(self):
        record = {"level": "warn", "msg": "warn: low disk"}
        result = highlight_record(record, keys=["level"], pattern="warn")
        assert ANSI["cyan"] in result
        assert ANSI["yellow"] in result

    def test_empty_record(self):
        assert highlight_record({}) == ""
