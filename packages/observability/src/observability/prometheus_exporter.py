"""Prometheus text exposition format exporter."""

from observability.counter import Counter
from observability.gauge import Gauge
from observability.registry import MetricsRegistry


def _escape_label_value(value: str) -> str:
    """Escape special characters in label values for Prometheus format.

    Prometheus requires escaping of:
    - backslash -> \\
    - newline -> \\n
    - double quote -> \\"

    Args:
        value: The label value to escape.

    Returns:
        The escaped label value.
    """
    # Order matters: escape backslashes first
    value = value.replace("\\", "\\\\")
    value = value.replace("\n", "\\n")
    value = value.replace('"', '\\"')
    return value


def _format_labels(labels: dict[str, str]) -> str:
    """Format labels dictionary into Prometheus label format.

    Args:
        labels: Dictionary of label name to value pairs.

    Returns:
        Formatted label string like {label1="value1",label2="value2"}
        or empty string if no labels.
    """
    if not labels:
        return ""

    parts = []
    for name, value in sorted(labels.items()):
        escaped_value = _escape_label_value(value)
        parts.append(f'{name}="{escaped_value}"')

    return "{" + ",".join(parts) + "}"


def _format_value(value: float) -> str:
    """Format a metric value for Prometheus output.

    Args:
        value: The numeric value to format.

    Returns:
        String representation of the value.
    """
    # If it's a whole number, format without decimal places
    if value == int(value):
        return str(int(value))
    return str(value)


def _get_metric_type(metric: object) -> str:
    """Determine the Prometheus type string for a metric.

    Args:
        metric: The metric instance.

    Returns:
        The Prometheus type string (counter, gauge, or untyped).
    """
    if isinstance(metric, Counter):
        return "counter"
    elif isinstance(metric, Gauge):
        return "gauge"
    return "untyped"


def format_prometheus(registry: MetricsRegistry) -> str:
    """Format all metrics in a registry as Prometheus text exposition format.

    The output follows the Prometheus text-based format:
    - # HELP <metric_name> <description>
    - # TYPE <metric_name> <type>
    - <metric_name>{<labels>} <value>

    Args:
        registry: The metrics registry to export.

    Returns:
        A string in Prometheus text exposition format.
    """
    lines: list[str] = []
    all_samples = registry.collect_all()

    for metric_name in sorted(all_samples.keys()):
        samples = all_samples[metric_name]
        metric = registry.get(metric_name)

        if metric is not None:
            # Add HELP line
            lines.append(f"# HELP {metric_name} {metric.description}")
            # Add TYPE line
            metric_type = _get_metric_type(metric)
            lines.append(f"# TYPE {metric_name} {metric_type}")

        # Add sample lines
        for sample in samples:
            label_str = _format_labels(sample.labels)
            value_str = _format_value(sample.value)
            lines.append(f"{metric_name}{label_str} {value_str}")

    return "\n".join(lines)
