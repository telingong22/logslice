import pytest
from logslice.merge import merge_streams, tag_source


def _r(ts, msg):
    return {"timestamp": ts, "msg": msg}


class TestMergeStreams:
    def test_two_streams_interleaved(self):
        a = [_r("2024-01-01T10:00:00", "a1"), _r("2024-01-01T10:02:00", "a2")]
        b = [_r("2024-01-01T10:01:00", "b1"), _r("2024-01-01T10:03:00", "b2")]
        result = list(merge_streams([a, b]))
        assert [r["msg"] for r in result] == ["a1", "b1", "a2", "b2"]

    def test_single_stream_unchanged(self):
        a = [_r("2024-01-01T09:00:00", "x"), _r("2024-01-01T10:00:00", "y")]
        result = list(merge_streams([a]))
        assert result == a

    def test_empty_streams(self):
        result = list(merge_streams([[], []]))
        assert result == []

    def test_one_empty_one_nonempty(self):
        a = [_r("2024-01-01T10:00:00", "only")]
        result = list(merge_streams([a, []]))
        assert len(result) == 1
        assert result[0]["msg"] == "only"

    def test_missing_timestamp_goes_last(self):
        a = [_r("2024-01-01T10:00:00", "first")]
        b = [{"msg": "no-ts"}]
        result = list(merge_streams([a, b]))
        assert result[0]["msg"] == "first"
        assert result[1]["msg"] == "no-ts"

    def test_missing_timestamp_goes_first_when_flag_set(self):
        a = [_r("2024-01-01T10:00:00", "later")]
        b = [{"msg": "no-ts"}]
        result = list(merge_streams([a, b], missing_last=False))
        assert result[0]["msg"] == "no-ts"

    def test_three_streams(self):
        a = [_r("2024-01-01T10:00:00", "a")]
        b = [_r("2024-01-01T10:01:00", "b")]
        c = [_r("2024-01-01T09:59:00", "c")]
        result = list(merge_streams([a, b, c]))
        assert [r["msg"] for r in result] == ["c", "a", "b"]


class TestTagSource:
    def test_adds_source_field(self):
        records = [{"msg": "hello"}]
        result = list(tag_source(records, "app1"))
        assert result[0]["_source"] == "app1"

    def test_does_not_mutate_original(self):
        original = {"msg": "hello"}
        list(tag_source([original], "app1"))
        assert "_source" not in original

    def test_custom_field(self):
        records = [{"msg": "x"}]
        result = list(tag_source(records, "svc", field="source"))
        assert result[0]["source"] == "svc"

    def test_empty_input(self):
        assert list(tag_source([], "x")) == []
