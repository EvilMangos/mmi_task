"""Tests for MetricsRegistry."""

from __future__ import annotations

import pytest

from observability.metrics.counter import Counter
from observability.metrics.gauge import Gauge
from observability.metrics.registry import MetricsRegistry


class TestMetricsRegistryBasic:
    """Tests for basic registry operations."""

    def test_register_and_get(self) -> None:
        """Registered metric can be retrieved by name."""
        registry = MetricsRegistry()
        counter = Counter(name="my_counter", description="Test counter")

        registry.register(counter)
        retrieved = registry.get("my_counter")

        assert retrieved is counter

    def test_get_returns_none_for_unknown(self) -> None:
        """get() returns None for unregistered metric names."""
        registry = MetricsRegistry()
        result = registry.get("unknown_metric")

        assert result is None


class TestMetricsRegistryDuplicates:
    """Tests for duplicate registration handling."""

    def test_register_duplicate_raises(self) -> None:
        """Registering a metric with an existing name raises an error."""
        registry = MetricsRegistry()
        counter1 = Counter(name="duplicate", description="First counter")
        counter2 = Counter(name="duplicate", description="Second counter")

        registry.register(counter1)

        with pytest.raises((ValueError, KeyError)):
            registry.register(counter2)


class TestMetricsRegistryUnregister:
    """Tests for unregistering metrics."""

    def test_unregister_removes(self) -> None:
        """unregister() removes a metric from the registry."""
        registry = MetricsRegistry()
        counter = Counter(name="removable", description="To be removed")

        registry.register(counter)
        assert registry.get("removable") is counter

        registry.unregister("removable")
        assert registry.get("removable") is None

    def test_unregister_unknown_is_silent(self) -> None:
        """unregister() for unknown metric does not raise."""
        registry = MetricsRegistry()

        # Should not raise
        registry.unregister("never_registered")


class TestMetricsRegistryCollectAll:
    """Tests for collecting all metrics."""

    def test_collect_all_aggregates(self) -> None:
        """collect_all() returns samples from all registered metrics."""
        registry = MetricsRegistry()

        counter = Counter(name="requests_total", description="Total requests")
        counter.inc(10.0)

        gauge = Gauge(name="active_connections", description="Active connections")
        gauge.set(5.0)

        registry.register(counter)
        registry.register(gauge)

        result = registry.collect_all()

        assert "requests_total" in result
        assert "active_connections" in result

        # Check values
        requests_samples = result["requests_total"]
        assert len(requests_samples) == 1
        assert requests_samples[0].value == 10.0

        connections_samples = result["active_connections"]
        assert len(connections_samples) == 1
        assert connections_samples[0].value == 5.0

    def test_collect_all_empty_registry(self) -> None:
        """collect_all() returns empty dict for empty registry."""
        registry = MetricsRegistry()
        result = registry.collect_all()

        assert result == {}
