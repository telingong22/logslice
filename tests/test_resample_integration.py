"""Integration tests: resample_records <-> cli_resample round-trip."""

import io
import json
import types

from logslice.resample import resample_records
from logslice.cli_resample import run_resample


def _make_args(**kwargs):
    defaults = {
        "interval": 60,
        "ts_field": "timestamp",
        "agg": "count",
        "value_field": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


RAW_RECORDS = [
    {"timestamp": "2024-06-01T10:00:05Z", "latency": 100},
    {"timestamp": "2024-06-01T10:00:35Z", "latency": 200},
    {"timestamp": "2024-06-01T10:01:10Z", "latency": 50},
    {"timestamp": "2024-06-01T10:02:00Z", "latency": 75},
]


class TestResampleIntegration:
    def test_count_matches_cli_output(self):
        """Direct call and CLI path should produce identical bucket counts."""
        direct = list(resample_records(RAW_RECORDS, 60))

        lines = [json.dumps(r) for r in RAW_RECORDS]
        stream = io.StringIO("\n".join(lines) + "\n")
        out = io.StringIO()
        run_resample(_make_args(), stream=stream, out=out)
        out.seek(0)
        cli_results = [json.loads(l) for l in out if l.strip()]

        assert len(direct) == len(cli_results)
        for d, c in zip(direct, cli_results):
            assert d["bucket"] == c["bucket"]
            assert d["count"] == c["count"]

    def test_avg_matches_cli_output(self):
        direct = list(
            resample_records(RAW_RECORDS, 60, agg="avg", value_field="latency")
        )

        lines = [json.dumps(r) for r in RAW_RECORDS]
        stream = io.StringIO("\n".join(lines) + "\n")
        out = io.StringIO()
        run_resample(
            _make_args(agg="avg", value_field="latency"),
            stream=stream,
            out=out,
        )
        out.seek(0)
        cli_results = [json.loads(l) for l in out if l.strip()]

        assert len(direct) == len(cli_results)
        for d, c in zip(direct, cli_results):
            assert abs(d["avg"] - c["avg"]) < 1e-9

    def test_three_buckets_correct_distribution(self):
        result = list(resample_records(RAW_RECORDS, 60))
        assert len(result) == 3
        counts = [r["count"] for r in result]
        assert counts == [2, 1, 1]

    def test_five_minute_bucket_collapses_all(self):
        result = list(resample_records(RAW_RECORDS, 300))
        assert len(result) == 1
        assert result[0]["count"] == 4
