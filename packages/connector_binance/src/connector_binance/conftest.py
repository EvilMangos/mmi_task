"""
Shared pytest fixtures for connector_binance tests.
"""

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest

from connector_binance.testing import BinanceMessageBuilder


@pytest.fixture
def binance_message_builder():
    """Factory fixture for creating BinanceMessageBuilder instances.

    Usage:
        def test_example(binance_message_builder):
            message = (
                binance_message_builder()
                .with_symbol("BTCUSDT")
                .with_bids([("42000.50", "1.5")])
                .build()
            )
    """
    return BinanceMessageBuilder


@pytest.fixture
def create_mock_websocket():
    """Fixture factory for creating mock WebSocket instances.

    Returns a callable that creates mock WebSocket objects with predefined messages.

    Usage:
        def test_example(create_mock_websocket):
            mock_ws = create_mock_websocket(["message1", "message2"])
    """

    def _create(
        messages: list[str],
        raise_on_recv_after: int | None = None,
        exception_to_raise: Exception | None = None,
    ) -> AsyncMock:
        """Create a mock WebSocket that yields predefined messages.

        Args:
            messages: List of message strings to yield
            raise_on_recv_after: If set, raises exception after this many messages
            exception_to_raise: Exception to raise (default: ConnectionError)
        """
        mock_ws = AsyncMock()
        mock_ws.close = AsyncMock()

        call_count = 0

        async def mock_recv() -> str:
            nonlocal call_count
            if raise_on_recv_after is not None and call_count >= raise_on_recv_after:
                raise exception_to_raise or ConnectionError("Connection lost")
            if call_count < len(messages):
                msg = messages[call_count]
                call_count += 1
                return msg
            # Block indefinitely if no more messages (simulates waiting)
            raise exception_to_raise or ConnectionError("No more messages")

        mock_ws.recv = mock_recv
        return mock_ws

    return _create


@pytest.fixture
def mock_websockets_connect(create_mock_websocket):
    """Fixture that provides a helper to set up mock WebSocket connections.

    This fixture consolidates the repeated pattern of patching websockets.connect
    and setting up a mock WebSocket with predefined messages.

    Usage:
        def test_example(mock_websockets_connect):
            with mock_websockets_connect(["message1", "message2"]) as (mock_ws, mock_websockets):
                # mock_ws is the mock WebSocket instance
                # mock_websockets is the patched websockets module
                await feed.start()
                mock_websockets.connect.assert_called_once()

        # With exception configuration:
        def test_error(mock_websockets_connect):
            with mock_websockets_connect(
                ["msg1"],
                raise_on_recv_after=1,
                exception_to_raise=ConnectionError("Lost")
            ) as (mock_ws, mock_websockets):
                ...
    """

    @contextmanager
    def _setup(
        messages: list[str],
        raise_on_recv_after: int | None = None,
        exception_to_raise: Exception | None = None,
    ):
        """Set up mock WebSocket connection with predefined messages.

        Args:
            messages: List of message strings the mock WebSocket will yield
            raise_on_recv_after: If set, raises exception after this many messages
            exception_to_raise: Exception to raise (default: ConnectionError)

        Yields:
            Tuple of (mock_ws, mock_websockets) for inspection and assertions
        """
        with patch("connector_binance.binance_feed.websockets") as mock_websockets:
            mock_ws = create_mock_websocket(
                messages,
                raise_on_recv_after=raise_on_recv_after,
                exception_to_raise=exception_to_raise,
            )
            mock_websockets.connect = AsyncMock(return_value=mock_ws)
            yield mock_ws, mock_websockets

    return _setup
