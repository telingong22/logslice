"""Tests for logslice.mask."""

import pytest
from logslice.mask import apply_masks, mask_field, mask_pattern


class TestMaskField:
    def test_fully_masks_by_default(self):
        r = {"token": "abcdef"}
        out = mask_field(r, "token")
        assert out["token"] == "******"

    def test_show_first(self):
        r = {"token": "abcdef"}
        out = mask_field(r, "token", show_first=2)
        assert out["token"] == "ab****"

    def test_show_last(self):
        r = {"token": "abcdef"}
        out = mask_field(r, "token", show_last=2)
        assert out["token"] == "****ef"

    def test_show_first_and_last(self):
        r = {"token": "abcdefgh"}
        out = mask_field(r, "token", show_first=2, show_last=2)
        assert out["token"] == "ab****gh"

    def test_custom_mask_char(self):
        r = {"pw": "secret"}
        out = mask_field(r, "pw", mask_char="#")
        assert out["pw"] == "######"

    def test_missing_field_returns_unchanged(self):
        r = {"other": "value"}
        out = mask_field(r, "token")
        assert out == r

    def test_does_not_mutate_original(self):
        r = {"token": "abcdef"}
        mask_field(r, "token", show_first=1)
        assert r["token"] == "abcdef"

    def test_non_string_value_coerced(self):
        r = {"code": 123456}
        out = mask_field(r, "code", show_first=1)
        assert out["code"] == "1*****"

    def test_show_first_exceeds_length(self):
        r = {"token": "ab"}
        out = mask_field(r, "token", show_first=10)
        assert out["token"] == "ab"

    def test_dotted_path(self):
        r = {"user": {"email": "alice@example.com"}}
        out = mask_field(r, "user.email", show_first=3)
        assert out["user"]["email"].startswith("ali")
        assert "*" in out["user"]["email"]


class TestMaskPattern:
    def test_replaces_matching_substring(self):
        r = {"msg": "token=abc123 sent"}
        out = mask_pattern(r, r"token=\w+")
        assert out["msg"] == "*** sent"

    def test_no_match_unchanged(self):
        r = {"msg": "hello world"}
        out = mask_pattern(r, r"\d+")
        assert out["msg"] == "hello world"

    def test_custom_replacement(self):
        r = {"msg": "pw=secret"}
        out = mask_pattern(r, r"pw=\S+", replacement="[REDACTED]")
        assert out["msg"] == "[REDACTED]"

    def test_nested_dict_values_masked(self):
        r = {"meta": {"note": "ssn=123456789"}}
        out = mask_pattern(r, r"ssn=\d+")
        assert out["meta"]["note"] == "***"

    def test_does_not_mutate_original(self):
        r = {"msg": "token=abc"}
        mask_pattern(r, r"token=\w+")
        assert r["msg"] == "token=abc"


class TestApplyMasks:
    def test_applies_field_mask_to_all_records(self):
        records = [{"pw": "secret"}, {"pw": "other"}]
        out = list(apply_masks(records, fields=["pw"]))
        assert all("*" in r["pw"] for r in out)

    def test_applies_pattern_to_all_records(self):
        records = [{"msg": "id=42"}, {"msg": "id=99"}]
        out = list(apply_masks(records, pattern=r"id=\d+"))
        assert all(r["msg"] == "***" for r in out)

    def test_empty_input_returns_empty(self):
        assert list(apply_masks([], fields=["x"])) == []
