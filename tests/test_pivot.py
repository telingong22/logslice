import pytest
from logslice.pivot import pivot_collect, pivot_count, pivot_to_records, pivot_records

RECORDS = [
    {"service": "api", "status": "200"},
    {"service": "api", "status": "500"},
    {"service": "worker", "status": "200"},
    {"service": "api", "status": "200"},
    {"service": "worker", "status": "404"},
]


class TestPivotCollect:
    def test_basic_collect(self):
        result = pivot_collect(RECORDS, "service", "status")
        assert sorted(result["api"]) == ["200", "200", "500"]
        assert sorted(result["worker"]) == ["200", "404"]

    def test_missing_key_ignored(self):
        records = [{"status": "200"}, {"service": "api", "status": "404"}]
        result = pivot_collect(records, "service", "status")
        assert list(result.keys()) == ["api"]

    def test_missing_value_ignored(self):
        records = [{"service": "api"}, {"service": "api", "status": "200"}]
        result = pivot_collect(records, "service", "status")
        assert result["api"] == ["200"]

    def test_empty_input(self):
        assert pivot_collect([], "service", "status") == {}


class TestPivotCount:
    def test_counts(self):
        result = pivot_count(RECORDS, "service", "status")
        assert result["api"] == 3
        assert result["worker"] == 2

    def test_empty(self):
        assert pivot_count([], "service", "status") == {}


class TestPivotToRecords:
    def _collected(self):
        return {"api": ["200", "500", "200"], "worker": ["200", "404"]}

    def test_list_aggregate(self):
        out = list(pivot_to_records(self._collected(), "service", "status", "list"))
        api = next(r for r in out if r["service"] == "api")
        assert sorted(api["status"]) == ["200", "200", "500"]

    def test_count_aggregate(self):
        out = list(pivot_to_records(self._collected(), "service", "status", "count"))
        api = next(r for r in out if r["service"] == "api")
        assert api["status"] == 3

    def test_first_aggregate(self):
        out = list(pivot_to_records(self._collected(), "service", "status", "first"))
        api = next(r for r in out if r["service"] == "api")
        assert api["status"] == "200"

    def test_last_aggregate(self):
        out = list(pivot_to_records(self._collected(), "service", "status", "last"))
        api = next(r for r in out if r["service"] == "api")
        assert api["status"] == "200"


class TestPivotRecords:
    def test_end_to_end_count(self):
        out = list(pivot_records(RECORDS, "service", "status", "count"))
        by_service = {r["service"]: r["status"] for r in out}
        assert by_service["api"] == 3
        assert by_service["worker"] == 2

    def test_end_to_end_list(self):
        out = list(pivot_records(RECORDS, "service", "status", "list"))
        by_service = {r["service"]: r["status"] for r in out}
        assert len(by_service["api"]) == 3
