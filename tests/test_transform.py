"""Tests for logslice.transform module."""

import pytest
from logslice.transform import (
    rename_fields,
    drop_fields,
    keep_fields,
    add_field,
    apply_transforms,
)

SAMPLE = {"level": "info", "msg": "hello", "ts": "2024-01-01T00:00:00Z", "user": "alice"}


class TestRenameFields:
    def test_basic_rename(self):
        result = rename_fields(SAMPLE, {"msg": "message", "ts": "timestamp"})
        assert "message" in result
        assert "timestamp" in result
        assert "msg" not in result
        assert "ts" not in result

    def test_no_match_unchanged(self):
        result = rename_fields(SAMPLE, {"nonexistent": "other"})
        assert result == SAMPLE

    def test_empty_renames(self):
        assert rename_fields(SAMPLE, {}) == SAMPLE


class TestDropFields:
    def test_drop_existing(self):
        result = drop_fields(SAMPLE, ["user", "ts"])
        assert "user" not in result
        assert "ts" not in result
        assert "level" in result

    def test_drop_nonexistent(self):
        result = drop_fields(SAMPLE, ["ghost"])
        assert result == SAMPLE

    def test_drop_all(self):
        result = drop_fields(SAMPLE, list(SAMPLE.keys()))
        assert result == {}


class TestKeepFields:
    def test_keep_subset(self):
        result = keep_fields(SAMPLE, ["level", "msg"])
        assert result == {"level": "info", "msg": "hello"}

    def test_keep_none_matching(self):
        result = keep_fields(SAMPLE, ["ghost"])
        assert result == {}


class TestAddField:
    def test_add_new(self):
        result = add_field(SAMPLE, "env", "prod")
        assert result["env"] == "prod"
        assert len(result) == len(SAMPLE) + 1

    def test_overwrite_existing(self):
        result = add_field(SAMPLE, "level", "error")
        assert result["level"] == "error"


class TestApplyTransforms:
    def test_chain(self):
        records = [dict(SAMPLE), dict(SAMPLE)]
        result = list(apply_transforms(records, renames={"msg": "message"}, drop=["user"]))
        assert len(result) == 2
        assert "message" in result[0]
        assert "user" not in result[0]

    def test_keep_only(self):
        records = [dict(SAMPLE)]
        result = list(apply_transforms(records, keep=["level"]))
        assert result == [{"level": "info"}]

    def test_no_transforms(self):
        records = [dict(SAMPLE)]
        result = list(apply_transforms(records))
        assert result == [dict(SAMPLE)]
