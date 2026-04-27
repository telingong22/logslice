"""Tests for logslice.correlate."""

import pytest
from logslice.correlate import (
    build_index,
    inner_join,
    left_join,
    correlate_records,
)


def _r(**kwargs):
    return dict(**kwargs)


class TestBuildIndex:
    def test_basic(self):
        records = [_r(id=1, x="a"), _r(id=2, x="b"), _r(id=1, x="c")]
        idx = build_index(records, "id")
        assert len(idx[1]) == 2
        assert len(idx[2]) == 1

    def test_missing_key_ignored(self):
        records = [_r(x=1), _r(id=2, x=2)]
        idx = build_index(records, "id")
        assert list(idx.keys()) == [2]

    def test_empty_input(self):
        assert build_index([], "id") == {}


class TestInnerJoin:
    def test_basic_join(self):
        left = [_r(id=1, val="L")]
        right = [_r(id=1, val="R")]
        result = list(inner_join(left, right, "id"))
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["left_val"] == "L"
        assert result[0]["right_val"] == "R"

    def test_no_match_yields_nothing(self):
        left = [_r(id=1, val="L")]
        right = [_r(id=2, val="R")]
        result = list(inner_join(left, right, "id"))
        assert result == []

    def test_multiple_right_matches(self):
        left = [_r(id=1, a=10)]
        right = [_r(id=1, b=20), _r(id=1, b=30)]
        result = list(inner_join(left, right, "id"))
        assert len(result) == 2
        assert {r["right_b"] for r in result} == {20, 30}

    def test_left_missing_key_skipped(self):
        left = [_r(val="no-key"), _r(id=1, val="has-key")]
        right = [_r(id=1, val="R")]
        result = list(inner_join(left, right, "id"))
        assert len(result) == 1


class TestLeftJoin:
    def test_unmatched_left_still_emitted(self):
        left = [_r(id=1, val="L")]
        right = [_r(id=2, val="R")]
        result = list(left_join(left, right, "id"))
        assert len(result) == 1
        assert result[0]["left_val"] == "L"
        assert "right_val" not in result[0]

    def test_matched_left_enriched(self):
        left = [_r(id=1, val="L")]
        right = [_r(id=1, val="R")]
        result = list(left_join(left, right, "id"))
        assert result[0]["right_val"] == "R"

    def test_missing_key_in_left_still_emitted(self):
        left = [_r(val="no-key")]
        right = [_r(id=1, val="R")]
        result = list(left_join(left, right, "id"))
        assert len(result) == 1
        assert result[0]["left_val"] == "no-key"


class TestCorrelateRecords:
    def test_inner_mode(self):
        left = [_r(id=1, x=1)]
        right = [_r(id=1, y=2)]
        result = list(correlate_records(left, right, "id", mode="inner"))
        assert len(result) == 1

    def test_left_mode(self):
        left = [_r(id=1, x=1), _r(id=99, x=2)]
        right = [_r(id=1, y=2)]
        result = list(correlate_records(left, right, "id", mode="left"))
        assert len(result) == 2

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown correlation mode"):
            list(correlate_records([], [], "id", mode="outer"))
