"""Core types for the metrics system."""

from dataclasses import dataclass
from typing import Protocol

Labels = dict[str, str]
"""Type alias for metric labels - a dictionary mapping label names to values."""


@dataclass(frozen=True)
class Sample:
    """A single metric sample with labels and a value.

    Attributes:
        labels: Dictionary of label name to label value pairs.
        value: The numeric value of this sample.
    """

    labels: Labels
    value: float


class Metric(Protocol):
    """Protocol defining the interface for all metric types.

    All metric implementations must provide:
    - name: The metric name
    - description: A human-readable description
    - labels: Tuple of label names this metric uses
    - collect(): Method to retrieve all current samples
    """

    @property
    def name(self) -> str:
        """The name of this metric."""
        ...

    @property
    def description(self) -> str:
        """A human-readable description of this metric."""
        ...

    @property
    def labels(self) -> tuple[str, ...]:
        """The label names this metric uses."""
        ...

    def collect(self) -> list[Sample]:
        """Collect all current samples from this metric.

        Returns:
            A list of Sample objects representing the current state.
        """
        ...
