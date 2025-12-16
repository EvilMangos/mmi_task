"""Observability package for logging, metrics, and tracing utilities."""

from observability.correlation import (
    correlation_context,
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)
from observability.debug import is_debug_enabled
from observability.exception_formatter import format_exception
from observability.json_formatter import JsonFormatter
from observability.logger_factory import get_logger
from observability.metrics import (
    Counter,
    Gauge,
    Labels,
    Metric,
    MetricsRegistry,
    Sample,
    format_prometheus,
)
from observability.timing import timed

__all__ = [
    # Debug
    "is_debug_enabled",
    # Correlation
    "correlation_context",
    "get_correlation_id",
    "reset_correlation_id",
    "set_correlation_id",
    # Exception formatting
    "format_exception",
    # JSON formatter
    "JsonFormatter",
    # Logger factory
    "get_logger",
    # Timing
    "timed",
    # Metrics types
    "Labels",
    "Metric",
    "Sample",
    # Counter
    "Counter",
    # Gauge
    "Gauge",
    # Registry
    "MetricsRegistry",
    # Prometheus exporter
    "format_prometheus",
]
