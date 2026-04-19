import pytest
from logslice.diff import diff_consecutive, diff_pair, changed_only


class TestDiffConsecutive:
    def test_first_record_has_empty_diff(self):
        records = [{"a": 1, "b": 2}]
        result = list(diff_consecutive(records))
        assert result[0]["_diff"] == []

    def test_changed_fields_detected(self):
        records = [{"a": 1, "b": 2}, {"a": 1, "b": 3}]
        result = list(diff_consecutive(records))
        assert result[1]["_diff"] == ["b"]

    def test_no_change_empty_diff(self):
        records = [{"a": 1}, {"a": 1}]
        result = list(diff_consecutive(records))
        assert result[1]["_diff"] == []

    def test_subset_fields(self):
        records = [{"a": 1, "b": 2}, {"a": 9, "b": 3}]
        result = list(diff_consecutive(records, fields=["b"]))
        assert result[1]["_diff"] == ["b"]

    def test_custom_tag_field(self):
        records = [{"x": 1}, {"x": 2}]
        result = list(diff_consecutive(records, tag_field="changes"))
        assert "changes" in result[1]

    def test_empty_input(self):
        assert list(diff_consecutive([])) == []

    def test_does_not_mutate_original(self):
        original = {"a": 1}
        list(diff_consecutive([original]))
        assert "_diff" not in original


class TestDiffPair:
    def test_single_difference(self):
        result = diff_pair({"a": 1, "b": 2}, {"a": 1, "b": 3})
        assert result == {"b": (2, 3)}

    def test_no_differences(self):
        assert diff_pair({"a": 1}, {"a": 1}) == {}

    def test_missing_key_in_b(self):
        result = diff_pair({"a": 1}, {})
        assert result == {"a": (1, None)}

    def test_fields_subset(self):
        result = diff_pair({"a": 1, "b": 9}, {"a": 2, "b": 9}, fields=["a"])
        assert "b" not in result
        assert result["a"] == (1, 2)


class TestChangedOnly:
    def test_first_record_always_included(self):
        records = [{"a": 1}]
        result = list(changed_only(records))
        assert len(result) == 1

    def test_unchanged_records_skipped(self):
        records = [{"a": 1}, {"a": 1}, {"a": 2}]
        result = list(changed_only(records))
        assert len(result) == 2

    def test_empty_input(self):
        assert list(changed_only([])) == []
