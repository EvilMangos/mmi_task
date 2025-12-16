"""Health endpoint server for orderbook watcher.

Provides /health and /metrics endpoints for monitoring and health checks.
This module is optional and only starts if HEALTH_PORT is configured.
"""

from typing import Any

from aiohttp import web
from observability import get_logger

logger = get_logger(__name__)


class HealthServer:
    """Simple HTTP server for health checks and metrics.

    Provides:
    - /health - Returns {"status": "healthy"} with 200 OK
    - /metrics - Returns basic metrics (placeholder for Prometheus format)
    """

    def __init__(self, port: int, host: str = "127.0.0.1") -> None:
        """Initialize the health server.

        Args:
            port: Port number to listen on.
            host: Host address to bind to (default: 127.0.0.1 for local-only access).
        """
        self._port = port
        self._host = host
        self._app = web.Application()
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

        # Register routes
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/metrics", self._handle_metrics)

        # Basic metrics
        self._snapshots_processed = 0
        self._alerts_sent = 0

    @property
    def snapshots_processed(self) -> int:
        """Number of snapshots processed."""
        return self._snapshots_processed

    @property
    def alerts_sent(self) -> int:
        """Number of alerts sent."""
        return self._alerts_sent

    def record_snapshot_processed(self) -> None:
        """Increment the snapshots processed counter."""
        self._snapshots_processed += 1

    def record_alert_sent(self) -> None:
        """Increment the alerts sent counter."""
        self._alerts_sent += 1

    async def _handle_health(self, _request: web.Request) -> web.Response:
        """Handle /health endpoint.

        Returns:
            JSON response with health status.
        """
        return web.json_response({"status": "healthy"})

    async def _handle_metrics(self, _request: web.Request) -> web.Response:
        """Handle /metrics endpoint.

        Returns:
            Prometheus-format metrics text.
        """
        metrics = (
            f"# HELP orderbook_watcher_snapshots_processed_total "
            f"Total number of order book snapshots processed\n"
            f"# TYPE orderbook_watcher_snapshots_processed_total counter\n"
            f"orderbook_watcher_snapshots_processed_total {self._snapshots_processed}\n"
            f"\n"
            f"# HELP orderbook_watcher_alerts_sent_total "
            f"Total number of alerts sent\n"
            f"# TYPE orderbook_watcher_alerts_sent_total counter\n"
            f"orderbook_watcher_alerts_sent_total {self._alerts_sent}\n"
        )
        return web.Response(text=metrics, content_type="text/plain")

    async def start(self) -> None:
        """Start the health server."""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()
        logger.info("Health server started on %s:%d", self._host, self._port)

    async def stop(self) -> None:
        """Stop the health server."""
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._site = None
            logger.info("Health server stopped")

    async def __aenter__(self) -> "HealthServer":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.stop()
