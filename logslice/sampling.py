"""Sampling utilities for logslice: rate-based and reservoir sampling."""

import random
from typing import Iterable, Iterator


def sample_rate(records: Iterable[dict], rate: float) -> Iterator[dict]:
    """Yield each record with probability `rate` (0.0 – 1.0)."""
    if not 0.0 < rate <= 1.0:
        raise ValueError(f"rate must be in (0, 1], got {rate}")
    for record in records:
        if random.random() < rate:
            yield record


def sample_every_n(records: Iterable[dict], n: int) -> Iterator[dict]:
    """Yield every nth record (1-based), i.e. keep 1 in every n."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for i, record in enumerate(records):
        if i % n == 0:
            yield record


def reservoir_sample(records: Iterable[dict], k: int) -> list:
    """Return a list of up to k records chosen uniformly at random."""
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    reservoir: list = []
    for i, record in enumerate(records):
        if i < k:
            reservoir.append(record)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = record
    return reservoir
