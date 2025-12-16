"""Tests for metrics types."""

from __future__ import annotations


class TestSample:
    """Tests for Sample dataclass."""

    def test_sample_creation(self) -> None:
        """Sample can be created with labels and value."""
        from observability.metrics_types import Sample

        sample = Sample(labels={"env": "prod", "region": "us-east"}, value=42.5)

        assert sample.labels == {"env": "prod", "region": "us-east"}
        assert sample.value == 42.5

    def test_sample_equality(self) -> None:
        """Two samples with same labels and value are equal."""
        from observability.metrics_types import Sample

        sample1 = Sample(labels={"key": "value"}, value=10.0)
        sample2 = Sample(labels={"key": "value"}, value=10.0)
        sample3 = Sample(labels={"key": "other"}, value=10.0)
        sample4 = Sample(labels={"key": "value"}, value=20.0)

        assert sample1 == sample2
        assert sample1 != sample3
        assert sample1 != sample4


class TestLabelsType:
    """Tests for Labels type alias."""

    def test_labels_is_dict_str_str(self) -> None:
        """Labels type accepts dict[str, str]."""
        from observability.metrics_types import Labels

        labels: Labels = {"service": "api", "version": "1.0"}

        assert labels["service"] == "api"
        assert labels["version"] == "1.0"


class TestMetricProtocol:
    """Tests for Metric protocol."""

    def test_metric_protocol_defines_required_methods(self) -> None:
        """Metric protocol has name, description, labels properties and collect method."""
        from observability.metrics_types import Metric, Sample

        # Create a class that implements the protocol
        class TestMetric:
            @property
            def name(self) -> str:
                return "test_metric"

            @property
            def description(self) -> str:
                return "A test metric"

            @property
            def labels(self) -> tuple[str, ...]:
                return ("label1", "label2")

            def collect(self) -> list[Sample]:
                return [Sample(labels={}, value=1.0)]

        # This should type-check as Metric
        metric: Metric = TestMetric()

        assert metric.name == "test_metric"
        assert metric.description == "A test metric"
        assert metric.labels == ("label1", "label2")
        assert len(metric.collect()) == 1
