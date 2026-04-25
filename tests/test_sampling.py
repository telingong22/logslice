"""Tests for logslice.sampling."""

import pytest
from logslice.sampling import sample_rate, sample_every_n, reservoir_sample

RECORDS = [{"i": i} for i in range(100)]


class TestSampleRate:
    def test_rate_one_keeps_all(self):
        result = list(sample_rate(RECORDS, 1.0))
        assert result == RECORDS

    def test_rate_zero_invalid(self):
        with pytest.raises(ValueError):
            list(sample_rate(RECORDS, 0.0))

    def test_rate_above_one_invalid(self):
        with pytest.raises(ValueError):
            list(sample_rate(RECORDS, 1.5))

    def test_rate_negative_invalid(self):
        with pytest.raises(ValueError):
            list(sample_rate(RECORDS, -0.5))

    def test_rate_half_roughly_half(self):
        import random
        random.seed(42)
        result = list(sample_rate(RECORDS, 0.5))
        assert 30 <= len(result) <= 70

    def test_empty_input(self):
        assert list(sample_rate([], 0.5)) == []


class TestSampleEveryN:
    def test_every_1_keeps_all(self):
        result = list(sample_every_n(RECORDS, 1))
        assert result == RECORDS

    def test_every_2_keeps_half(self):
        result = list(sample_every_n(RECORDS, 2))
        assert len(result) == 50
        assert result[0] == {"i": 0}
        assert result[1] == {"i": 2}

    def test_every_10(self):
        result = list(sample_every_n(RECORDS, 10))
        assert len(result) == 10

    def test_n_zero_invalid(self):
        with pytest.raises(ValueError):
            list(sample_every_n(RECORDS, 0))

    def test_n_negative_invalid(self):
        with pytest.raises(ValueError):
            list(sample_every_n(RECORDS, -1))

    def test_empty_input(self):
        assert list(sample_every_n([], 5)) == []


class TestReservoirSample:
    def test_k_larger_than_input(self):
        result = reservoir_sample(RECORDS[:5], 20)
        assert len(result) == 5

    def test_k_exact(self):
        result = reservoir_sample(RECORDS, 10)
        assert len(result) == 10

    def test_all_results_are_original_records(self):
        result = reservoir_sample(RECORDS, 20)
        for r in result:
            assert r in RECORDS

    def test_k_zero_invalid(self):
        with pytest.raises(ValueError):
            reservoir_sample(RECORDS, 0)

    def test_k_negative_invalid(self):
        with pytest.raises(ValueError):
            reservoir_sample(RECORDS, -5)

    def test_empty_input(self):
        assert reservoir_sample([], 5) == []
