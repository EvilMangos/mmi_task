"""Base class for metric implementations."""

import threading
from abc import ABC

from observability.metrics.types import Labels, Sample


class BaseMetric(ABC):
    """Abstract base class providing shared functionality for metrics.

    This class implements common behavior for all metric types including:
    - Thread-safe value storage with labels
    - Label-to-key conversion
    - Sample collection

    Subclasses must implement their specific mutation methods (inc, dec, set, etc.).
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

    def collect(self) -> list[Sample]:
        """Collect all current samples from this metric.

        Returns:
            A list of Sample objects representing the current state.
        """
        with self._lock:
            samples = []
            for key, value in self._values.items():
                labels_dict = dict(key)
                samples.append(Sample(labels=labels_dict, value=value))
            return samples
