"""Counter metric implementation."""

import threading
from typing import Mapping

from observability.metrics_types import Labels, Sample


class Counter:
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

    def collect(self) -> list[Sample]:
        """Collect all current samples from this counter.

        Returns:
            A list of Sample objects representing the current state.
        """
        with self._lock:
            samples = []
            for key, value in self._values.items():
                labels_dict = dict(key)
                samples.append(Sample(labels=labels_dict, value=value))
            return samples
