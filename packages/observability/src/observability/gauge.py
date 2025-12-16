"""Gauge metric implementation."""

from typing import Mapping

from observability.base_metric import BaseMetric
from observability.metrics_types import Labels


class Gauge(BaseMetric):
    """A gauge metric that can go up and down.

    Gauges represent a current value that can increase or decrease,
    such as temperature, memory usage, or number of active connections.

    Args:
        name: The metric name.
        description: A human-readable description.
        label_names: Optional tuple of label names this gauge uses.

    Example:
        gauge = Gauge("active_connections", "Current active connections", ("server",))
        gauge.set(10, labels={"server": "web1"})
        gauge.inc(labels={"server": "web1"})
        gauge.dec(labels={"server": "web1"})
    """

    def set(
        self,
        value: float,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Set the gauge to the given value.

        Args:
            value: The value to set.
            labels: Optional label values.
        """
        labels_dict: Labels = dict(labels) if labels is not None else {}
        key = self._labels_to_key(labels_dict)

        with self._lock:
            self._values[key] = value

    def inc(
        self,
        value: float = 1.0,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Increment the gauge by the given value.

        Args:
            value: The amount to increment by. Default is 1.0.
            labels: Optional label values.
        """
        labels_dict: Labels = dict(labels) if labels is not None else {}
        key = self._labels_to_key(labels_dict)

        with self._lock:
            current = self._values.get(key, 0.0)
            self._values[key] = current + value

    def dec(
        self,
        value: float = 1.0,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Decrement the gauge by the given value.

        Args:
            value: The amount to decrement by. Default is 1.0.
            labels: Optional label values.
        """
        labels_dict: Labels = dict(labels) if labels is not None else {}
        key = self._labels_to_key(labels_dict)

        with self._lock:
            current = self._values.get(key, 0.0)
            self._values[key] = current - value
