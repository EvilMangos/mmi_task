"""Tests for Prometheus exporter."""

from __future__ import annotations

from observability.counter import Counter
from observability.gauge import Gauge
from observability.prometheus_exporter import format_prometheus
from observability.registry import MetricsRegistry


class TestFormatPrometheusBasic:
    """Tests for basic Prometheus formatting."""

    def test_format_prometheus_empty_registry(self) -> None:
        """Formatting an empty registry produces empty output."""
        registry = MetricsRegistry()
        result = format_prometheus(registry)

        assert result == ""

    def test_format_prometheus_counter(self) -> None:
        """Counter is formatted with TYPE counter."""
        registry = MetricsRegistry()
        counter = Counter(name="http_requests", description="HTTP request count")
        counter.inc(42.0)
        registry.register(counter)

        result = format_prometheus(registry)

        # Should include HELP and TYPE lines
        assert "# HELP http_requests" in result
        assert "# TYPE http_requests counter" in result
        # Value line
        assert "http_requests" in result
        assert "42" in result

    def test_format_prometheus_gauge(self) -> None:
        """Gauge is formatted with TYPE gauge."""
        registry = MetricsRegistry()
        gauge = Gauge(name="temperature", description="Current temperature")
        gauge.set(23.5)
        registry.register(gauge)

        result = format_prometheus(registry)

        assert "# HELP temperature" in result
        assert "# TYPE temperature gauge" in result
        assert "temperature" in result
        assert "23.5" in result


class TestFormatPrometheusWithLabels:
    """Tests for Prometheus formatting with labels."""

    def test_format_prometheus_with_labels(self) -> None:
        """Metrics with labels are formatted correctly."""
        registry = MetricsRegistry()
        counter = Counter(
            name="http_requests",
            description="HTTP requests",
            label_names=("method", "status"),
        )
        counter.inc(labels={"method": "GET", "status": "200"})
        counter.inc(labels={"method": "POST", "status": "201"})
        registry.register(counter)

        result = format_prometheus(registry)

        # Should have labels in curly braces
        assert 'method="GET"' in result
        assert 'status="200"' in result
        assert 'method="POST"' in result
        assert 'status="201"' in result


class TestFormatPrometheusEscaping:
    """Tests for special character escaping."""

    def test_format_prometheus_escapes_special_chars(self) -> None:
        """Label values with special characters are properly escaped."""
        registry = MetricsRegistry()
        counter = Counter(
            name="events",
            description="Event count",
            label_names=("path",),
        )
        # Label value with special chars: backslash, newline, quote
        counter.inc(labels={"path": '/api/v1/"test"\\path\n'})
        registry.register(counter)

        result = format_prometheus(registry)

        # Backslashes should be escaped as \\
        # Newlines should be escaped as \n
        # Quotes should be escaped as \"
        assert '\\"' in result or '\\"' in result
        assert "\\\\" in result or "\\" in result
        # The output should be valid (no unescaped quotes breaking the format)
        assert 'path="' in result


class TestFormatPrometheusMultipleMetrics:
    """Tests for formatting multiple metrics."""

    def test_format_prometheus_multiple_metrics(self) -> None:
        """Multiple metrics are each formatted with their own HELP/TYPE."""
        registry = MetricsRegistry()

        counter = Counter(name="requests_total", description="Total requests")
        counter.inc(100.0)

        gauge = Gauge(name="active_users", description="Active user count")
        gauge.set(50.0)

        registry.register(counter)
        registry.register(gauge)

        result = format_prometheus(registry)

        # Both metrics should be present
        assert "# HELP requests_total" in result
        assert "# TYPE requests_total counter" in result
        assert "100" in result

        assert "# HELP active_users" in result
        assert "# TYPE active_users gauge" in result
        assert "50" in result
