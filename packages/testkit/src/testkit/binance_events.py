"""Synthetic Binance websocket event generator for testing."""

from typing import TypedDict

# Fixed timestamp for deterministic tests: 2024-01-01 00:00:00 UTC in milliseconds
_DEFAULT_INITIAL_TIMESTAMP = 1704067200000


class DepthUpdateEvent(TypedDict):
    """Binance depth update websocket event structure."""

    e: str  # Event type: "depthUpdate"
    E: int  # Event timestamp (ms)
    s: str  # Symbol
    b: list[list[str]]  # Bids: [[price, qty], ...]
    a: list[list[str]]  # Asks: [[price, qty], ...]


class SnapshotResponse(TypedDict):
    """Binance REST API snapshot response structure."""

    lastUpdateId: int
    bids: list[list[str]]  # [[price, qty], ...]
    asks: list[list[str]]  # [[price, qty], ...]


class BinanceEvents:
    """Generate synthetic Binance protocol events for testing."""

    def __init__(self, initial_timestamp: int | None = None) -> None:
        """Initialize event generator with auto-incrementing counters.

        Args:
            initial_timestamp: Starting timestamp in milliseconds.
                Defaults to 1704067200000 (2024-01-01 00:00:00 UTC).
        """
        if initial_timestamp is None:
            initial_timestamp = _DEFAULT_INITIAL_TIMESTAMP
        self._timestamp_counter = initial_timestamp
        self._update_id_counter = 1

    def depth_update(
        self,
        symbol: str,
        bids: list[tuple[str, str]],
        asks: list[tuple[str, str]],
        timestamp: int | None = None,
    ) -> DepthUpdateEvent:
        """Generate a depth update event.

        Args:
            symbol: Trading pair symbol.
            bids: List of (price, qty) tuples as strings.
            asks: List of (price, qty) tuples as strings.
            timestamp: Optional custom timestamp (ms). Auto-increments if None.

        Returns:
            Binance depthUpdate event dict.
        """
        if timestamp is None:
            timestamp = self._timestamp_counter
            self._timestamp_counter += 100

        return {
            "e": "depthUpdate",
            "E": timestamp,
            "s": symbol,
            "b": [[price, qty] for price, qty in bids],
            "a": [[price, qty] for price, qty in asks],
        }

    def snapshot(
        self,
        symbol: str,
        bids: list[tuple[str, str]],
        asks: list[tuple[str, str]],
        last_update_id: int | None = None,
    ) -> SnapshotResponse:
        """Generate a snapshot response.

        Args:
            symbol: Trading pair symbol (not included in response).
            bids: List of (price, qty) tuples as strings.
            asks: List of (price, qty) tuples as strings.
            last_update_id: Optional custom lastUpdateId. Auto-increments if None.

        Returns:
            Binance snapshot response dict.
        """
        if last_update_id is None:
            last_update_id = self._update_id_counter
            self._update_id_counter += 1

        return {
            "lastUpdateId": last_update_id,
            "bids": [[price, qty] for price, qty in bids],
            "asks": [[price, qty] for price, qty in asks],
        }

    def sequence(
        self,
        symbol: str,
        updates: list[dict],
        start_timestamp: int | None = None,
        timestamp_increment: int = 100,
    ) -> list[DepthUpdateEvent]:
        """Generate a sequence of depth update events.

        Args:
            symbol: Trading pair symbol.
            updates: List of dicts with 'bids' and 'asks' keys.
            start_timestamp: Optional starting timestamp (ms).
            timestamp_increment: Time increment between events (ms).

        Returns:
            List of Binance depthUpdate events.
        """
        if not updates:
            return []

        if start_timestamp is None:
            current_timestamp = self._timestamp_counter
        else:
            current_timestamp = start_timestamp

        events = []
        for update in updates:
            event = self.depth_update(
                symbol=symbol,
                bids=update.get("bids", []),
                asks=update.get("asks", []),
                timestamp=current_timestamp,
            )
            events.append(event)
            current_timestamp += timestamp_increment

        return events
