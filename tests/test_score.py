"""Tests for logslice.score."""
import pytest

from logslice.score import score_field_match, threshold_filter, top_scoring


def _r(**kw):
    return dict(kw)


# ---------------------------------------------------------------------------
# score_field_match
# ---------------------------------------------------------------------------

class TestScoreFieldMatch:
    def test_single_rule_match(self):
        records = [_r(level="error")]
        rules = [("level", "error", 10.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 10.0

    def test_single_rule_no_match(self):
        records = [_r(level="info")]
        rules = [("level", "error", 10.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 0.0

    def test_multiple_rules_cumulative(self):
        records = [_r(level="error", service="auth")]
        rules = [("level", "error", 5.0), ("service", "auth", 3.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 8.0

    def test_base_score_added(self):
        records = [_r(level="info")]
        rules = []
        result = list(score_field_match(records, rules, base=1.0))
        assert result[0]["_score"] == 1.0

    def test_callable_predicate(self):
        records = [_r(latency=250)]
        rules = [("latency", lambda v: v is not None and v > 200, 7.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 7.0

    def test_callable_predicate_no_match(self):
        records = [_r(latency=100)]
        rules = [("latency", lambda v: v is not None and v > 200, 7.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 0.0

    def test_nested_field(self):
        records = [_r(meta={"env": "prod"})]
        rules = [("meta.env", "prod", 4.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 4.0

    def test_missing_field_no_score(self):
        records = [_r(other="x")]
        rules = [("level", "error", 5.0)]
        result = list(score_field_match(records, rules))
        assert result[0]["_score"] == 0.0

    def test_custom_score_field(self):
        records = [_r(level="error")]
        rules = [("level", "error", 1.0)]
        result = list(score_field_match(records, rules, score_field="relevance"))
        assert "relevance" in result[0]
        assert result[0]["relevance"] == 1.0

    def test_does_not_mutate_original(self):
        original = _r(level="error")
        rules = [("level", "error", 5.0)]
        list(score_field_match([original], rules))
        assert "_score" not in original

    def test_empty_input(self):
        assert list(score_field_match([], [("level", "error", 1.0)])) == []


# ---------------------------------------------------------------------------
# threshold_filter
# ---------------------------------------------------------------------------

class TestThresholdFilter:
    def _scored(self, *scores):
        return [{"_score": s} for s in scores]

    def test_min_score_filters_low(self):
        result = list(threshold_filter(self._scored(1.0, 5.0, 10.0), min_score=5.0))
        assert [r["_score"] for r in result] == [5.0, 10.0]

    def test_max_score_filters_high(self):
        result = list(threshold_filter(self._scored(1.0, 5.0, 10.0), max_score=5.0))
        assert [r["_score"] for r in result] == [1.0, 5.0]

    def test_both_bounds(self):
        result = list(threshold_filter(self._scored(1.0, 5.0, 10.0), min_score=2.0, max_score=8.0))
        assert [r["_score"] for r in result] == [5.0]

    def test_no_bounds_passes_all(self):
        result = list(threshold_filter(self._scored(1.0, 5.0)))
        assert len(result) == 2

    def test_missing_score_treated_as_zero(self):
        result = list(threshold_filter([{}], min_score=1.0))
        assert result == []


# ---------------------------------------------------------------------------
# top_scoring
# ---------------------------------------------------------------------------

class TestTopScoring:
    def _scored(self, *scores):
        return [{"_score": s} for s in scores]

    def test_returns_top_n(self):
        result = top_scoring(self._scored(3.0, 1.0, 5.0, 2.0), n=2)
        assert [r["_score"] for r in result] == [5.0, 3.0]

    def test_n_larger_than_input(self):
        result = top_scoring(self._scored(1.0, 2.0), n=10)
        assert len(result) == 2

    def test_invalid_n_raises(self):
        with pytest.raises(ValueError):
            top_scoring([], n=0)

    def test_empty_input(self):
        assert top_scoring([], n=1) == []
