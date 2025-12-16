"""Binance WebSocket feed for order book data."""

import asyncio
import json
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Self

import websockets
from config import BinanceSettings
from domain_orderbook import OrderBookSnapshot
from observability import get_logger
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed

from connector_binance.backoff import ExponentialBackoff
from connector_binance.exceptions import ParseError
from connector_binance.message_parser import parse_depth_message

logger = get_logger(__name__)

_BINANCE_DEPTH_LEVELS: tuple[int, ...] = (5, 10, 20)


class BinanceFeed:
    """Async feed for Binance order book data via WebSocket.

    Manages a WebSocket connection to Binance and yields OrderBookSnapshot
    instances for configured symbols. Handles reconnection with exponential
    backoff on connection errors.

    Usage:
        async with BinanceFeed(settings) as feed:
            async for snapshot in feed.snapshots():
                process(snapshot)
    """

    def __init__(self, settings: BinanceSettings) -> None:
        """Initialize the Binance feed.

        Args:
            settings: Binance configuration settings.
        """
        self._settings = settings
        self._ws: ClientConnection | None = None
        self._running = False
        self._backoff = ExponentialBackoff()

    def _determine_depth_level(self) -> int:
        """Map top_n_levels to smallest sufficient Binance depth level."""
        for level in _BINANCE_DEPTH_LEVELS:
            if self._settings.top_n_levels <= level:
                return level
        return _BINANCE_DEPTH_LEVELS[-1]

    def _build_stream_url(self) -> str:
        """Build the combined stream WebSocket URL.

        Returns:
            Full WebSocket URL with all symbol streams.
        """
        depth_level = self._determine_depth_level()

        # Build stream names: btcusdt@depth10, dotusdt@depth10, etc.
        streams = [
            f"{symbol.lower()}@depth{depth_level}" for symbol in self._settings.symbols
        ]

        # Combined stream URL format: ws_url/stream?streams=stream1/stream2/...
        base_url = self._settings.ws_url.rstrip("/")
        # Change /ws to /stream for combined streams
        if base_url.endswith("/ws"):
            base_url = base_url.removesuffix("/ws") + "/stream"

        stream_path = "/".join(streams)
        return f"{base_url}?streams={stream_path}"

    async def start(self) -> None:
        """Start the WebSocket connection.

        This method is idempotent - calling it multiple times will not
        create multiple connections.
        """
        if self._ws is not None:
            return  # Already connected

        self._running = True
        await self._connect()

    async def _connect(self) -> None:
        """Establish WebSocket connection with retry on failure."""
        while self._running:
            try:
                url = self._build_stream_url()
                self._ws = await websockets.connect(url)
                self._backoff.reset()
                logger.info("Connected to Binance WebSocket: %s", url)
                return
            except Exception as e:
                if not self._running:
                    return
                delay = self._backoff.next_delay()
                logger.warning("Connection failed (%s), retrying in %.1fs", e, delay)
                await asyncio.sleep(delay)

    async def stop(self) -> None:
        """Stop the WebSocket connection.

        This method is idempotent - calling it multiple times is safe.
        """
        self._running = False

        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception as e:
                logger.debug("Ignoring exception during WebSocket close: %s", e)
            self._ws = None

    async def snapshots(self) -> AsyncIterator[OrderBookSnapshot]:
        """Yield order book snapshots from the WebSocket stream.

        Yields:
            OrderBookSnapshot instances as they are received.

        Note:
            This is an async generator that will keep yielding until
            stop() is called or a fatal error occurs.
        """
        while self._running:
            if self._ws is None:
                await self._connect()
                if self._ws is None:
                    return  # Was stopped during connect

            try:
                message_str = await self._ws.recv()
                snapshot = self._parse_message(message_str)
                if snapshot is not None:
                    yield snapshot
            except (ConnectionClosed, ConnectionError) as e:
                if not self._running:
                    return
                logger.warning("Connection lost (%s), reconnecting...", e)
                self._ws = None
                await self._connect()
            except Exception as e:
                if not self._running:
                    return
                logger.error("Unexpected error in snapshot loop: %s", e)
                self._ws = None
                await self._connect()

    def _parse_message(self, message_str: str) -> OrderBookSnapshot | None:
        """Parse a raw message string into an OrderBookSnapshot.

        Args:
            message_str: Raw JSON message from WebSocket.

        Returns:
            OrderBookSnapshot if successfully parsed, None if message
            should be skipped (e.g., malformed).
        """
        try:
            message: dict[str, Any] = json.loads(message_str)
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON received: %s", e)
            return None

        try:
            return parse_depth_message(message)
        except ParseError as e:
            logger.warning("Failed to parse depth message: %s", e)
            return None

    async def __aenter__(self) -> Self:
        """Async context manager entry - starts the connection."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit - stops the connection."""
        await self.stop()
