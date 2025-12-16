"""
Tests for BinanceFeed - TDD RED stage.

These tests define the expected behavior of the BinanceFeed class that
manages WebSocket connections to Binance and yields OrderBookSnapshot instances.

Requirements covered:
    R1: start() initiates WebSocket connection
    R2: URL includes all symbols in combined stream format
    R3: Messages from WS are parsed and yielded as snapshots
    R4: Connection errors trigger reconnect with backoff
    R5: stop() closes connection and stops iteration
    R6: Multiple stop() calls are safe (idempotent)
    R7: AsyncIterator exits cleanly after stop()
    R8: Malformed messages log warning and continue (no crash)
"""

import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from config import BinanceSettings
from domain_orderbook import OrderBookSnapshot

# These imports will fail until implementation exists (RED stage)
from connector_binance.binance_feed import BinanceFeed

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def binance_settings() -> BinanceSettings:
    """Standard Binance settings for testing."""
    return BinanceSettings(
        symbols=["BTCUSDT", "DOTUSDT", "SOLUSDT"],
        ws_url="wss://stream.binance.com:9443/ws",
        top_n_levels=10,
    )


@pytest.fixture
def single_symbol_settings() -> BinanceSettings:
    """Binance settings with a single symbol."""
    return BinanceSettings(
        symbols=["BTCUSDT"],
        ws_url="wss://stream.binance.com:9443/ws",
        top_n_levels=5,
    )


@pytest.fixture
def sample_btcusdt_message() -> str:
    """Sample Binance combined stream message for BTCUSDT."""
    return json.dumps(
        {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 12345,
                "bids": [
                    ["42000.50", "1.5"],
                    ["42000.00", "2.0"],
                ],
                "asks": [
                    ["42001.00", "0.5"],
                    ["42001.50", "1.0"],
                ],
            },
        }
    )


@pytest.fixture
def sample_dotusdt_message() -> str:
    """Sample Binance combined stream message for DOTUSDT."""
    return json.dumps(
        {
            "stream": "dotusdt@depth10",
            "data": {
                "lastUpdateId": 67890,
                "bids": [
                    ["7.50", "100"],
                ],
                "asks": [
                    ["7.51", "50"],
                ],
            },
        }
    )


@pytest.fixture
def malformed_message() -> str:
    """Malformed JSON message missing required fields."""
    return json.dumps(
        {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                # missing bids and asks
            },
        }
    )


@pytest.fixture
def invalid_json_message() -> str:
    """Invalid JSON string."""
    return "not valid json {"


# =============================================================================
# Category 1: Connection (R1)
# =============================================================================


class TestConnection:
    """Tests for WebSocket connection behavior."""

    @pytest.mark.asyncio
    async def test_start_connects_to_websocket(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R1: Calling start() initiates WS connection."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()

            mock_websockets.connect.assert_called_once()
            await feed.stop()

    @pytest.mark.asyncio
    async def test_start_is_idempotent(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R1: Multiple start() calls do not create multiple connections."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()
            await feed.start()  # Second call
            await feed.start()  # Third call

            # Should only connect once
            assert mock_websockets.connect.call_count == 1
            await feed.stop()


# =============================================================================
# Category 2: URL Construction (R2)
# =============================================================================


class TestUrlConstruction:
    """Tests for combined stream URL building."""

    @pytest.mark.asyncio
    async def test_builds_correct_combined_stream_url(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R2: URL includes all symbols in correct combined stream format."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()

            # Get the URL that was used
            call_args = mock_websockets.connect.call_args
            url = call_args[0][0] if call_args[0] else call_args[1].get("uri")

            # URL should be combined stream format:
            # wss://stream.binance.com:9443/stream?streams=btcusdt@depth10/dotusdt@depth10/solusdt@depth10
            assert "btcusdt@depth" in url.lower()
            assert "dotusdt@depth" in url.lower()
            assert "solusdt@depth" in url.lower()
            await feed.stop()

    @pytest.mark.asyncio
    async def test_single_symbol_url_format(
        self, single_symbol_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R2: Single symbol URL is correctly formatted."""
        feed = BinanceFeed(settings=single_symbol_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()

            call_args = mock_websockets.connect.call_args
            url = call_args[0][0] if call_args[0] else call_args[1].get("uri")

            assert "btcusdt@depth" in url.lower()
            await feed.stop()

    @pytest.mark.asyncio
    async def test_url_includes_depth_level_from_settings(
        self, single_symbol_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R2: URL includes correct depth level from top_n_levels."""
        feed = BinanceFeed(settings=single_symbol_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()

            call_args = mock_websockets.connect.call_args
            url = call_args[0][0] if call_args[0] else call_args[1].get("uri")

            # top_n_levels=5, so should use depth5
            assert "depth5" in url.lower() or "depth10" in url.lower()
            await feed.stop()


# =============================================================================
# Category 3: Message Parsing and Yielding (R3)
# =============================================================================


class TestSnapshotYielding:
    """Tests for parsing messages and yielding snapshots."""

    @pytest.mark.asyncio
    async def test_snapshots_yields_parsed_messages(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """R3: Messages from WS are parsed and yielded as OrderBookSnapshot."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([sample_btcusdt_message]) as (
            mock_ws,
            mock_websockets,
        ):
            await feed.start()

            snapshots: list[OrderBookSnapshot] = []
            async for snapshot in feed.snapshots():
                snapshots.append(snapshot)
                break  # Stop after first message

            assert len(snapshots) == 1
            assert isinstance(snapshots[0], OrderBookSnapshot)
            assert snapshots[0].symbol == "BTCUSDT"
            await feed.stop()

    @pytest.mark.asyncio
    async def test_yields_multiple_snapshots(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        sample_dotusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """R3: Multiple messages are yielded as snapshots."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect(
            [sample_btcusdt_message, sample_dotusdt_message]
        ) as (
            mock_ws,
            mock_websockets,
        ):
            await feed.start()

            snapshots: list[OrderBookSnapshot] = []
            count = 0
            async for snapshot in feed.snapshots():
                snapshots.append(snapshot)
                count += 1
                if count >= 2:
                    break

            assert len(snapshots) == 2
            symbols = {s.symbol for s in snapshots}
            assert "BTCUSDT" in symbols
            assert "DOTUSDT" in symbols
            await feed.stop()

    @pytest.mark.asyncio
    async def test_snapshots_returns_async_iterator(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R3: snapshots() returns an AsyncIterator."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()

            iterator = feed.snapshots()
            assert isinstance(iterator, AsyncIterator)
            await feed.stop()


# =============================================================================
# Category 4: Reconnection (R4)
# =============================================================================


class TestReconnection:
    """Tests for reconnection behavior on errors."""

    @pytest.mark.asyncio
    async def test_connection_error_triggers_reconnect(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        create_mock_websocket,
    ) -> None:
        """R4: On connection error, reconnects with backoff."""
        feed = BinanceFeed(settings=binance_settings)

        connection_attempts = 0

        with patch("connector_binance.binance_feed.websockets") as mock_websockets:
            # First connection fails, second succeeds
            async def connect_side_effect(*args, **kwargs):
                nonlocal connection_attempts
                connection_attempts += 1
                if connection_attempts == 1:
                    raise ConnectionError("First connection failed")
                return create_mock_websocket([sample_btcusdt_message])

            mock_websockets.connect = AsyncMock(side_effect=connect_side_effect)

            # Mock time.sleep to avoid actual delays
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await feed.start()

                # Should have retried
                assert connection_attempts >= 2

            await feed.stop()

    @pytest.mark.asyncio
    async def test_recv_error_triggers_reconnect(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        create_mock_websocket,
    ) -> None:
        """R4: Error during recv triggers reconnect."""
        feed = BinanceFeed(settings=binance_settings)

        reconnect_count = 0

        with patch("connector_binance.binance_feed.websockets") as mock_websockets:

            def create_ws():
                nonlocal reconnect_count
                reconnect_count += 1
                if reconnect_count == 1:
                    # First connection: yields one message then fails
                    return create_mock_websocket(
                        [sample_btcusdt_message],
                        raise_on_recv_after=1,
                    )
                # Second connection works
                return create_mock_websocket([sample_btcusdt_message])

            mock_websockets.connect = AsyncMock(side_effect=lambda *a, **k: create_ws())

            with patch("asyncio.sleep", new_callable=AsyncMock):
                await feed.start()

                snapshots = []
                async for snapshot in feed.snapshots():
                    snapshots.append(snapshot)
                    if len(snapshots) >= 2:
                        break

                # Should have reconnected
                assert reconnect_count >= 2

            await feed.stop()


# =============================================================================
# Category 5: Stop Behavior (R5)
# =============================================================================


class TestStopBehavior:
    """Tests for stop() behavior."""

    @pytest.mark.asyncio
    async def test_stop_closes_connection(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R5: stop() closes WS connection."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()
            await feed.stop()

            mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """R6: Multiple stop() calls are safe."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            await feed.start()

            # Multiple stops should not raise
            await feed.stop()
            await feed.stop()
            await feed.stop()

            # close should only be called once (or be idempotent)
            assert mock_ws.close.call_count >= 1

    @pytest.mark.asyncio
    async def test_stop_before_start_is_safe(
        self, binance_settings: BinanceSettings
    ) -> None:
        """R6: stop() on never-started feed is safe."""
        feed = BinanceFeed(settings=binance_settings)

        # Should not raise
        await feed.stop()


# =============================================================================
# Category 6: Iterator Cleanup (R7)
# =============================================================================


class TestIteratorCleanup:
    """Tests for clean iterator exit."""

    @pytest.mark.asyncio
    async def test_snapshots_stops_when_feed_stopped(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """R7: AsyncIterator exits cleanly after stop()."""
        feed = BinanceFeed(settings=binance_settings)

        # Create a websocket that will keep yielding
        messages = [sample_btcusdt_message] * 100
        with mock_websockets_connect(messages) as (mock_ws, mock_websockets):
            await feed.start()

            received_count = 0
            async for snapshot in feed.snapshots():
                received_count += 1
                if received_count == 2:
                    await feed.stop()
                    break

            # Should exit cleanly
            assert received_count == 2

    @pytest.mark.asyncio
    async def test_iterator_can_be_restarted_after_stop(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        create_mock_websocket,
    ) -> None:
        """R7: Feed can be restarted after stop."""
        feed = BinanceFeed(settings=binance_settings)

        with patch("connector_binance.binance_feed.websockets") as mock_websockets:
            mock_ws = create_mock_websocket([sample_btcusdt_message])
            mock_websockets.connect = AsyncMock(return_value=mock_ws)

            # First session
            await feed.start()
            await feed.stop()

            # Reset mock for second session
            mock_ws2 = create_mock_websocket([sample_btcusdt_message])
            mock_websockets.connect = AsyncMock(return_value=mock_ws2)

            # Second session
            await feed.start()

            async for snapshot in feed.snapshots():
                assert snapshot.symbol == "BTCUSDT"
                break

            await feed.stop()


# =============================================================================
# Category 7: Malformed Message Handling (R8)
# =============================================================================


class TestMalformedMessageHandling:
    """Tests for handling malformed messages."""

    @pytest.mark.asyncio
    async def test_malformed_message_logs_warning_continues(
        self,
        binance_settings: BinanceSettings,
        malformed_message: str,
        sample_btcusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """R8: Bad messages don't crash, just log warning and continue."""
        feed = BinanceFeed(settings=binance_settings)

        # First message is malformed, second is valid
        with mock_websockets_connect([malformed_message, sample_btcusdt_message]) as (
            mock_ws,
            mock_websockets,
        ):
            await feed.start()

            with patch("connector_binance.binance_feed.logger") as mock_logger:
                snapshots = []
                async for snapshot in feed.snapshots():
                    snapshots.append(snapshot)
                    if len(snapshots) >= 1:
                        break

                # Should have received the valid message
                assert len(snapshots) == 1
                assert snapshots[0].symbol == "BTCUSDT"

                # Should have logged a warning for malformed message
                mock_logger.warning.assert_called()

            await feed.stop()

    @pytest.mark.asyncio
    async def test_invalid_json_logs_warning_continues(
        self,
        binance_settings: BinanceSettings,
        invalid_json_message: str,
        sample_btcusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """R8: Invalid JSON logs warning and continues."""
        feed = BinanceFeed(settings=binance_settings)

        with mock_websockets_connect(
            [invalid_json_message, sample_btcusdt_message]
        ) as (
            mock_ws,
            mock_websockets,
        ):
            await feed.start()

            with patch("connector_binance.binance_feed.logger") as mock_logger:
                snapshots = []
                async for snapshot in feed.snapshots():
                    snapshots.append(snapshot)
                    if len(snapshots) >= 1:
                        break

                assert len(snapshots) == 1
                mock_logger.warning.assert_called()

            await feed.stop()

    @pytest.mark.asyncio
    async def test_multiple_malformed_messages_handled(
        self,
        binance_settings: BinanceSettings,
        malformed_message: str,
        sample_btcusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """R8: Multiple consecutive malformed messages handled gracefully."""
        feed = BinanceFeed(settings=binance_settings)

        messages = [
            malformed_message,
            malformed_message,
            malformed_message,
            sample_btcusdt_message,
        ]
        with mock_websockets_connect(messages) as (mock_ws, mock_websockets):
            await feed.start()

            with patch("connector_binance.binance_feed.logger"):
                snapshots = []
                async for snapshot in feed.snapshots():
                    snapshots.append(snapshot)
                    break

                # Should still get the valid message
                assert len(snapshots) == 1
                assert snapshots[0].symbol == "BTCUSDT"

            await feed.stop()


# =============================================================================
# Context Manager Support
# =============================================================================


class TestContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_async_context_manager_support(
        self,
        binance_settings: BinanceSettings,
        sample_btcusdt_message: str,
        mock_websockets_connect,
    ) -> None:
        """Feed supports async context manager (async with)."""
        with mock_websockets_connect([sample_btcusdt_message]) as (
            mock_ws,
            mock_websockets,
        ):
            async with BinanceFeed(settings=binance_settings) as feed:
                async for snapshot in feed.snapshots():
                    assert snapshot.symbol == "BTCUSDT"
                    break

            # Connection should be closed after exiting context
            mock_ws.close.assert_called()

    @pytest.mark.asyncio
    async def test_context_manager_handles_exceptions(
        self, binance_settings: BinanceSettings, mock_websockets_connect
    ) -> None:
        """Context manager cleans up on exception."""
        with mock_websockets_connect([]) as (mock_ws, mock_websockets):
            with pytest.raises(ValueError):
                async with BinanceFeed(settings=binance_settings) as _:
                    raise ValueError("Test exception")

            # Should still clean up
            mock_ws.close.assert_called()
