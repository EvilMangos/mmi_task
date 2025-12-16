"""Test support: Binance message builder for test data."""

from typing import Any, Self


class BinanceMessageBuilder:
    """Fluent builder for Binance depth message test data.

    Provides a clean API for constructing test messages without verbose dict literals.

    Usage:
        # Combined stream format (default)
        message = (
            BinanceMessageBuilder()
            .with_symbol("BTCUSDT")
            .with_bids([("42000.50", "1.5")])
            .with_asks([("42001.00", "0.5")])
            .build()
        )

        # Single stream format
        message = (
            BinanceMessageBuilder()
            .with_bids([("42000.50", "1.5")])
            .with_asks([("42001.00", "0.5")])
            .build_single_stream()
        )
    """

    def __init__(self) -> None:
        self._stream = "btcusdt@depth10"
        self._last_update_id = 100
        self._bids: list[list[str]] = []
        self._asks: list[list[str]] = []

    def with_stream(self, stream: str) -> Self:
        """Set the raw stream name (e.g., 'btcusdt@depth10')."""
        self._stream = stream
        return self

    def with_symbol(self, symbol: str, depth: int = 10) -> Self:
        """Set stream from symbol (e.g., 'BTCUSDT' -> 'btcusdt@depth10')."""
        self._stream = f"{symbol.lower()}@depth{depth}"
        return self

    def with_last_update_id(self, last_update_id: int) -> Self:
        """Set the lastUpdateId field."""
        self._last_update_id = last_update_id
        return self

    def with_bids(self, bids: list[tuple[str, str]]) -> Self:
        """Set bid levels as list of (price, qty) tuples."""
        self._bids = [[price, qty] for price, qty in bids]
        return self

    def with_asks(self, asks: list[tuple[str, str]]) -> Self:
        """Set ask levels as list of (price, qty) tuples."""
        self._asks = [[price, qty] for price, qty in asks]
        return self

    def build(self) -> dict[str, Any]:
        """Build combined stream format message (with stream + data wrapper)."""
        return {
            "stream": self._stream,
            "data": {
                "lastUpdateId": self._last_update_id,
                "bids": self._bids,
                "asks": self._asks,
            },
        }

    def build_single_stream(self) -> dict[str, Any]:
        """Build single stream format message (no wrapper)."""
        return {
            "lastUpdateId": self._last_update_id,
            "bids": self._bids,
            "asks": self._asks,
        }

    def build_without_data(self) -> dict[str, Any]:
        """Build combined stream format without 'data' key (for error tests)."""
        return {"stream": self._stream}

    def build_without_bids(self) -> dict[str, Any]:
        """Build combined stream format without 'bids' key (for error tests)."""
        return {
            "stream": self._stream,
            "data": {
                "lastUpdateId": self._last_update_id,
                "asks": self._asks,
            },
        }

    def build_without_asks(self) -> dict[str, Any]:
        """Build combined stream format without 'asks' key (for error tests)."""
        return {
            "stream": self._stream,
            "data": {
                "lastUpdateId": self._last_update_id,
                "bids": self._bids,
            },
        }
