"""Observability package for logging, metrics, and tracing utilities."""

from observability.correlation import (
    correlation_context,
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)
from observability.counter import Counter
from observability.debug import is_debug_enabled
from observability.exception_formatter import format_exception
from observability.gauge import Gauge
from observability.json_formatter import JsonFormatter
from observability.logger_factory import get_logger
from observability.metrics_types import Labels, Metric, Sample
from observability.prometheus_exporter import format_prometheus
from observability.registry import MetricsRegistry
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
