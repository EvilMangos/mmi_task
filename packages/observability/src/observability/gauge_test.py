"""Tests for Gauge metric."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor


class TestGaugeBasic:
    """Tests for basic Gauge functionality."""

    def test_gauge_starts_at_zero(self) -> None:
        """A new gauge starts with value zero."""
        from observability.gauge import Gauge

        gauge = Gauge(name="test_gauge", description="A test gauge")
        samples = gauge.collect()

        assert len(samples) == 1
        assert samples[0].value == 0.0

    def test_gauge_set_replaces_value(self) -> None:
        """set() replaces the current value."""
        from observability.gauge import Gauge

        gauge = Gauge(name="test_gauge", description="A test gauge")

        gauge.set(10.0)
        assert gauge.collect()[0].value == 10.0

        gauge.set(5.0)
        assert gauge.collect()[0].value == 5.0

        gauge.set(100.0)
        assert gauge.collect()[0].value == 100.0

    def test_gauge_inc_adds(self) -> None:
        """inc() adds to the current value."""
        from observability.gauge import Gauge

        gauge = Gauge(name="test_gauge", description="A test gauge")

        gauge.inc(5.0)
        assert gauge.collect()[0].value == 5.0

        gauge.inc(3.0)
        assert gauge.collect()[0].value == 8.0

        # Default increment is 1.0
        gauge.inc()
        assert gauge.collect()[0].value == 9.0

    def test_gauge_dec_subtracts(self) -> None:
        """dec() subtracts from the current value."""
        from observability.gauge import Gauge

        gauge = Gauge(name="test_gauge", description="A test gauge")
        gauge.set(10.0)

        gauge.dec(3.0)
        assert gauge.collect()[0].value == 7.0

        gauge.dec(2.0)
        assert gauge.collect()[0].value == 5.0

        # Default decrement is 1.0
        gauge.dec()
        assert gauge.collect()[0].value == 4.0

    def test_gauge_can_go_negative(self) -> None:
        """Gauge can have negative values."""
        from observability.gauge import Gauge

        gauge = Gauge(name="test_gauge", description="A test gauge")

        gauge.set(-5.0)
        assert gauge.collect()[0].value == -5.0

        gauge.dec(10.0)
        assert gauge.collect()[0].value == -15.0

        gauge.inc(5.0)
        assert gauge.collect()[0].value == -10.0


class TestGaugeWithLabels:
    """Tests for Gauge with labels."""

    def test_gauge_with_labels(self) -> None:
        """Gauge supports separate values per label combination."""
        from observability.gauge import Gauge

        gauge = Gauge(
            name="temperature",
            description="Temperature readings",
            label_names=("location", "unit"),
        )

        gauge.set(25.0, labels={"location": "office", "unit": "celsius"})
        gauge.set(77.0, labels={"location": "office", "unit": "fahrenheit"})
        gauge.set(20.0, labels={"location": "warehouse", "unit": "celsius"})

        samples = gauge.collect()

        assert len(samples) == 3

        # Find samples by labels
        office_celsius = next(
            s for s in samples if s.labels == {"location": "office", "unit": "celsius"}
        )
        office_fahrenheit = next(
            s for s in samples if s.labels == {"location": "office", "unit": "fahrenheit"}
        )
        warehouse_celsius = next(
            s for s in samples if s.labels == {"location": "warehouse", "unit": "celsius"}
        )

        assert office_celsius.value == 25.0
        assert office_fahrenheit.value == 77.0
        assert warehouse_celsius.value == 20.0


class TestGaugeThreadSafety:
    """Tests for Gauge thread safety."""

    def test_gauge_is_thread_safe(self) -> None:
        """Gauge can be safely modified from multiple threads."""
        from observability.gauge import Gauge

        gauge = Gauge(name="concurrent_gauge", description="Concurrent test")
        num_threads = 10
        operations_per_thread = 1000
        barrier = threading.Barrier(num_threads)

        def modify_gauge() -> None:
            barrier.wait()  # All threads start simultaneously to maximize contention
            for i in range(operations_per_thread):
                if i % 2 == 0:
                    gauge.inc(1.0)
                else:
                    gauge.dec(1.0)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(modify_gauge) for _ in range(num_threads)]
            for f in futures:
                f.result()

        samples = gauge.collect()
        # Each thread does 500 inc and 500 dec, net effect is 0
        # With 10 threads, total should be 0
        assert samples[0].value == 0.0
