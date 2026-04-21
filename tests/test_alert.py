"""Tests for logslice.alert."""
import pytest
from logslice.alert import check_threshold, alert_records, annotate_alerts


class TestCheckThreshold:
    def test_gt_true(self):
        assert check_threshold({"latency": 120}, "latency", "gt", 100) is True

    def test_gt_false(self):
        assert check_threshold({"latency": 80}, "latency", "gt", 100) is False

    def test_gte_equal(self):
        assert check_threshold({"latency": 100}, "latency", "gte", 100) is True

    def test_lt_true(self):
        assert check_threshold({"score": 0.3}, "score", "lt", 0.5) is True

    def test_lte_true(self):
        assert check_threshold({"score": 0.5}, "score", "lte", 0.5) is True

    def test_eq_true(self):
        assert check_threshold({"code": 200}, "code", "eq", 200) is True

    def test_ne_true(self):
        assert check_threshold({"code": 404}, "code", "ne", 200) is True

    def test_missing_field_returns_false(self):
        assert check_threshold({}, "latency", "gt", 0) is False

    def test_non_numeric_returns_false(self):
        assert check_threshold({"latency": "fast"}, "latency", "gt", 0) is False

    def test_nested_field(self):
        assert check_threshold({"http": {"status": 500}}, "http.status", "gte", 500) is True

    def test_unknown_op_raises(self):
        with pytest.raises(ValueError, match="Unknown operator"):
            check_threshold({"x": 1}, "x", "between", 0)

    def test_string_numeric_coerced(self):
        assert check_threshold({"count": "42"}, "count", "gt", 40) is True


class TestAlertRecords:
    _records = [
        {"latency": 50, "errors": 0},
        {"latency": 150, "errors": 0},
        {"latency": 200, "errors": 5},
    ]

    def test_single_rule_filters(self):
        rules = [("latency", "gt", 100)]
        result = list(alert_records(self._records, rules))
        assert len(result) == 2

    def test_match_all_requires_both(self):
        rules = [("latency", "gt", 100), ("errors", "gt", 0)]
        result = list(alert_records(self._records, rules, match_all=True))
        assert result == [{"latency": 200, "errors": 5}]

    def test_match_any_either_rule(self):
        rules = [("latency", "gt", 100), ("errors", "gt", 0)]
        result = list(alert_records(self._records, rules, match_all=False))
        assert len(result) == 2

    def test_empty_rules_yields_nothing(self):
        result = list(alert_records(self._records, []))
        assert result == []

    def test_empty_records(self):
        result = list(alert_records([], [("latency", "gt", 0)]))
        assert result == []


class TestAnnotateAlerts:
    def test_fired_flag_added(self):
        records = [{"latency": 200}, {"latency": 50}]
        rules = [("latency", "gt", 100)]
        result = list(annotate_alerts(records, rules))
        assert result[0]["_alert"] is True
        assert result[1]["_alert"] is False

    def test_custom_label(self):
        records = [{"x": 10}]
        result = list(annotate_alerts(records, [("x", "gt", 5)], label="fired"))
        assert result[0]["fired"] is True

    def test_original_fields_preserved(self):
        records = [{"latency": 200, "service": "api"}]
        result = list(annotate_alerts(records, [("latency", "gt", 100)]))
        assert result[0]["service"] == "api"

    def test_does_not_mutate_original(self):
        rec = {"latency": 200}
        list(annotate_alerts([rec], [("latency", "gt", 0)]))
        assert "_alert" not in rec
