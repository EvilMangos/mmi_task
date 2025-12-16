"""Counter metric implementation."""

from typing import Mapping

from observability.base_metric import BaseMetric
from observability.metrics_types import Labels


class Counter(BaseMetric):
    """A monotonically increasing counter metric.

    Counters can only increase (or be reset). They are typically used
    to count events like requests, errors, or items processed.

    Args:
        name: The metric name.
        description: A human-readable description.
        label_names: Optional tuple of label names this counter uses.

    Example:
        counter = Counter("requests_total", "Total requests", ("method", "status"))
        counter.inc(labels={"method": "GET", "status": "200"})
    """

    def inc(
        self,
        value: float = 1.0,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Increment the counter by the given value.

        Args:
            value: The amount to increment by. Must be non-negative.
            labels: Optional label values for this increment.

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError("Counter increment must be non-negative")

        labels_dict: Labels = dict(labels) if labels is not None else {}
        key = self._labels_to_key(labels_dict)

        with self._lock:
            current = self._values.get(key, 0.0)
            self._values[key] = current + value
