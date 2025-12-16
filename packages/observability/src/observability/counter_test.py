"""Tests for Counter metric."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from observability.counter import Counter


class TestCounterBasic:
    """Tests for basic Counter functionality."""

    def test_counter_starts_at_zero(self) -> None:
        """A new counter starts with value zero."""
        counter = Counter(name="test_counter", description="A test counter")
        samples = counter.collect()

        assert len(samples) == 1
        assert samples[0].value == 0.0

    def test_counter_inc_adds_value(self) -> None:
        """inc() adds the specified value to the counter."""
        counter = Counter(name="test_counter", description="A test counter")

        counter.inc(5.0)
        counter.inc(3.0)

        samples = counter.collect()
        assert samples[0].value == 8.0

    def test_counter_inc_default_one(self) -> None:
        """inc() with no arguments adds 1.0."""
        counter = Counter(name="test_counter", description="A test counter")

        counter.inc()
        counter.inc()
        counter.inc()

        samples = counter.collect()
        assert samples[0].value == 3.0


class TestCounterWithLabels:
    """Tests for Counter with labels."""

    def test_counter_inc_with_labels(self) -> None:
        """inc() with labels creates separate counters per label combination."""
        counter = Counter(
            name="http_requests",
            description="HTTP request count",
            label_names=("method", "status"),
        )

        counter.inc(labels={"method": "GET", "status": "200"})
        counter.inc(labels={"method": "GET", "status": "200"})
        counter.inc(labels={"method": "POST", "status": "201"})

        samples = counter.collect()

        # Should have 2 samples (2 label combinations)
        assert len(samples) == 2

        # Find samples by labels
        get_200 = next(
            s for s in samples if s.labels == {"method": "GET", "status": "200"}
        )
        post_201 = next(
            s for s in samples if s.labels == {"method": "POST", "status": "201"}
        )

        assert get_200.value == 2.0
        assert post_201.value == 1.0

    def test_counter_collect_returns_all_label_combinations(self) -> None:
        """collect() returns samples for all observed label combinations."""
        counter = Counter(
            name="events",
            description="Event count",
            label_names=("type",),
        )

        counter.inc(labels={"type": "click"})
        counter.inc(labels={"type": "scroll"})
        counter.inc(labels={"type": "hover"})
        counter.inc(labels={"type": "click"})

        samples = counter.collect()

        assert len(samples) == 3

        labels_to_values = {tuple(s.labels.items()): s.value for s in samples}
        assert labels_to_values[(("type", "click"),)] == 2.0
        assert labels_to_values[(("type", "scroll"),)] == 1.0
        assert labels_to_values[(("type", "hover"),)] == 1.0


class TestCounterValidation:
    """Tests for Counter input validation."""

    def test_counter_inc_negative_raises(self) -> None:
        """inc() with negative value raises ValueError."""
        counter = Counter(name="test_counter", description="A test counter")

        with pytest.raises(ValueError, match="negative|positive|must be"):
            counter.inc(-1.0)


class TestCounterThreadSafety:
    """Tests for Counter thread safety."""

    def test_counter_is_thread_safe(self) -> None:
        """Counter can be safely incremented from multiple threads."""
        counter = Counter(name="concurrent_counter", description="Concurrent test")
        num_threads = 10
        increments_per_thread = 1000
        barrier = threading.Barrier(num_threads)

        def increment_many() -> None:
            barrier.wait()  # All threads start simultaneously to maximize contention
            for _ in range(increments_per_thread):
                counter.inc()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(increment_many) for _ in range(num_threads)]
            for f in futures:
                f.result()

        samples = counter.collect()
        expected = num_threads * increments_per_thread
        assert samples[0].value == expected
