"""Tests for logslice.redact."""

import pytest
from logslice.redact import (
    redact_fields,
    redact_pattern,
    redact_nested,
    apply_redactions,
)

MASK = "***"


class TestRedactFields:
    def test_basic_redact(self):
        rec = {"user": "alice", "msg": "hello"}
        assert redact_fields(rec, ["user"]) == {"user": MASK, "msg": "hello"}

    def test_missing_field_ignored(self):
        rec = {"msg": "hello"}
        result = redact_fields(rec, ["password"])
        assert result == {"msg": "hello"}

    def test_multiple_fields(self):
        rec = {"a": 1, "b": 2, "c": 3}
        result = redact_fields(rec, ["a", "c"])
        assert result == {"a": MASK, "b": 2, "c": MASK}

    def test_does_not_mutate_original(self):
        rec = {"user": "alice"}
        redact_fields(rec, ["user"])
        assert rec["user"] == "alice"


class TestRedactPattern:
    def test_replaces_match(self):
        rec = {"msg": "token=abc123 ok"}
        result = redact_pattern(rec, r"token=\w+")
        assert result["msg"] == "*** ok"

    def test_non_string_values_untouched(self):
        rec = {"count": 42, "msg": "hello 42"}
        result = redact_pattern(rec, r"\d+")
        assert result["count"] == 42
        assert result["msg"] == "hello ***"

    def test_custom_replacement(self):
        rec = {"email": "user@example.com"}
        result = redact_pattern(rec, r"[^@]+@[^@]+", replacement="[REDACTED]")
        assert result["email"] == "[REDACTED]"


class TestRedactNested:
    def test_nested_redact(self):
        rec = {"user": {"name": "alice", "token": "secret"}}
        result = redact_nested(rec, "user.token")
        assert result["user"]["token"] == MASK
        assert result["user"]["name"] == "alice"

    def test_missing_path_unchanged(self):
        rec = {"user": {"name": "alice"}}
        result = redact_nested(rec, "user.password")
        assert "password" not in result["user"]

    def test_does_not_mutate_original(self):
        rec = {"a": {"b": "secret"}}
        redact_nested(rec, "a.b")
        assert rec["a"]["b"] == "secret"


class TestApplyRedactions:
    def test_pipeline(self):
        records = [
            {"user": "alice", "msg": "token=xyz"},
            {"user": "bob", "msg": "ok"},
        ]
        results = list(
            apply_redactions(records, fields=["user"], pattern=r"token=\w+")
        )
        assert results[0]["user"] == MASK
        assert results[0]["msg"] == "***"
        assert results[1]["user"] == MASK

    def test_nested_in_pipeline(self):
        records = [{"meta": {"ip": "1.2.3.4", "id": 1}}]
        results = list(apply_redactions(records, nested_paths=["meta.ip"]))
        assert results[0]["meta"]["ip"] == MASK
        assert results[0]["meta"]["id"] == 1
