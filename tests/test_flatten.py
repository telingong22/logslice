import pytest
from logslice.flatten import flatten_record, unflatten_record


class TestFlattenRecord:
    def test_already_flat(self):
        rec = {"level": "info", "msg": "hello"}
        assert flatten_record(rec) == {"level": "info", "msg": "hello"}

    def test_single_level_nesting(self):
        rec = {"http": {"method": "GET", "status": 200}}
        assert flatten_record(rec) == {"http.method": "GET", "http.status": 200}

    def test_deep_nesting(self):
        rec = {"a": {"b": {"c": 42}}}
        assert flatten_record(rec) == {"a.b.c": 42}

    def test_mixed_flat_and_nested(self):
        rec = {"ts": "2024-01-01", "user": {"id": 1, "name": "alice"}}
        result = flatten_record(rec)
        assert result["ts"] == "2024-01-01"
        assert result["user.id"] == 1
        assert result["user.name"] == "alice"

    def test_custom_separator(self):
        rec = {"http": {"status": 404}}
        assert flatten_record(rec, sep="_") == {"http_status": 404}

    def test_max_depth_one(self):
        rec = {"a": {"b": {"c": 1}}}
        result = flatten_record(rec, max_depth=1)
        assert result == {"a.b": {"c": 1}}

    def test_empty_record(self):
        assert flatten_record({}) == {}

    def test_does_not_mutate_original(self):
        rec = {"x": {"y": 99}}
        _ = flatten_record(rec)
        assert rec == {"x": {"y": 99}}

    def test_list_value_not_flattened(self):
        rec = {"tags": ["a", "b"]}
        assert flatten_record(rec) == {"tags": ["a", "b"]}


class TestUnflattenRecord:
    def test_basic_unflatten(self):
        rec = {"http.method": "GET", "http.status": 200}
        assert unflatten_record(rec) == {"http": {"method": "GET", "status": 200}}

    def test_already_flat(self):
        rec = {"level": "info", "msg": "hi"}
        assert unflatten_record(rec) == {"level": "info", "msg": "hi"}

    def test_deep_keys(self):
        rec = {"a.b.c": 42}
        assert unflatten_record(rec) == {"a": {"b": {"c": 42}}}

    def test_roundtrip(self):
        original = {"user": {"id": 7, "meta": {"role": "admin"}}}
        assert unflatten_record(flatten_record(original)) == original

    def test_empty_input(self):
        assert unflatten_record({}) == {}
