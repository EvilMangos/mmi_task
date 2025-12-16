"""Gauge metric implementation."""

import threading
from typing import Mapping

from observability.metrics_types import Labels, Sample


class Gauge:
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

    def __init__(
        self,
        name: str,
        description: str,
        label_names: tuple[str, ...] = (),
    ) -> None:
        self._name = name
        self._description = description
        self._label_names = label_names
        self._values: dict[tuple[tuple[str, str], ...], float] = {}
        self._lock = threading.Lock()
        # Initialize default (no labels) value to 0 only if no label names are defined
        if not label_names:
            self._values[tuple()] = 0.0

    @property
    def name(self) -> str:
        """The name of this metric."""
        return self._name

    @property
    def description(self) -> str:
        """A human-readable description of this metric."""
        return self._description

    @property
    def labels(self) -> tuple[str, ...]:
        """The label names this metric uses."""
        return self._label_names

    def _labels_to_key(self, labels: Labels | None) -> tuple[tuple[str, str], ...]:
        """Convert labels dict to a hashable key."""
        if labels is None:
            labels = {}
        # Sort by label name for consistent ordering
        return tuple(sorted(labels.items()))

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

    def collect(self) -> list[Sample]:
        """Collect all current samples from this gauge.

        Returns:
            A list of Sample objects representing the current state.
        """
        with self._lock:
            samples = []
            for key, value in self._values.items():
                labels_dict = dict(key)
                samples.append(Sample(labels=labels_dict, value=value))
            return samples
