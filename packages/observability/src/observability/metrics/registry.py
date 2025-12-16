"""Metrics registry for managing metric instances."""

from observability.metrics.types import Metric, Sample


class MetricsRegistry:
    """A registry for managing metric instances.

    The registry stores metrics by name and provides methods to
    register, unregister, and collect metrics.

    Example:
        registry = MetricsRegistry()
        counter = Counter("requests_total", "Total requests")
        registry.register(counter)
        all_samples = registry.collect_all()
    """

    def __init__(self) -> None:
        self._metrics: dict[str, Metric] = {}

    def register(self, metric: Metric) -> None:
        """Register a metric with the registry.

        Args:
            metric: The metric to register.

        Raises:
            ValueError: If a metric with the same name is already registered.
        """
        if metric.name in self._metrics:
            raise ValueError(f"Metric '{metric.name}' is already registered")
        self._metrics[metric.name] = metric

    def unregister(self, name: str) -> None:
        """Unregister a metric by name.

        This is a no-op if the metric is not found.

        Args:
            name: The name of the metric to unregister.
        """
        self._metrics.pop(name, None)

    def get(self, name: str) -> Metric | None:
        """Get a metric by name.

        Args:
            name: The name of the metric to retrieve.

        Returns:
            The metric if found, None otherwise.
        """
        return self._metrics.get(name)

    def collect_all(self) -> dict[str, list[Sample]]:
        """Collect samples from all registered metrics.

        Returns:
            A dictionary mapping metric names to their list of samples.
        """
        result: dict[str, list[Sample]] = {}
        for name, metric in self._metrics.items():
            result[name] = metric.collect()
        return result
