"""Unit tests for the HealthServer class."""

import pytest

from orderbook_watcher.health import HealthServer


class TestHealthServer:
    """Tests for HealthServer."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self) -> None:
        """GET /health returns 200 with healthy status."""
        server = HealthServer(port=0)

        # Test the handler directly (passing None as request since it's not used)
        response = await server._handle_health(None)  # type: ignore[arg-type]

        assert response.status == 200
        assert response.content_type == "application/json"

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_prometheus_format(self) -> None:
        """GET /metrics returns Prometheus-format text."""
        server = HealthServer(port=0)

        response = await server._handle_metrics(None)  # type: ignore[arg-type]

        assert response.status == 200
        assert response.content_type == "text/plain"
        text = response.text
        assert "orderbook_watcher_snapshots_processed_total" in text
        assert "orderbook_watcher_alerts_sent_total" in text

    @pytest.mark.asyncio
    async def test_record_snapshot_processed(self) -> None:
        """record_snapshot_processed increments counter."""
        server = HealthServer(port=0)

        assert server.snapshots_processed == 0
        server.record_snapshot_processed()
        assert server.snapshots_processed == 1
        server.record_snapshot_processed()
        assert server.snapshots_processed == 2

    @pytest.mark.asyncio
    async def test_record_alert_sent(self) -> None:
        """record_alert_sent increments counter."""
        server = HealthServer(port=0)

        assert server.alerts_sent == 0
        server.record_alert_sent()
        assert server.alerts_sent == 1

    @pytest.mark.asyncio
    async def test_metrics_reflect_counters(self) -> None:
        """Metrics endpoint reflects actual counter values."""
        server = HealthServer(port=0)

        server.record_snapshot_processed()
        server.record_snapshot_processed()
        server.record_alert_sent()

        response = await server._handle_metrics(None)  # type: ignore[arg-type]
        text = response.text

        assert "orderbook_watcher_snapshots_processed_total 2" in text
        assert "orderbook_watcher_alerts_sent_total 1" in text

    def test_initial_counters_are_zero(self) -> None:
        """Initial counter values are zero."""
        server = HealthServer(port=8080)

        assert server.snapshots_processed == 0
        assert server.alerts_sent == 0
