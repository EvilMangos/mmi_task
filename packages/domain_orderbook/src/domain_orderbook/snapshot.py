"""OrderBookSnapshot dataclass representing a point-in-time order book state."""

from dataclasses import dataclass

from domain_orderbook.level import OrderBookLevel


@dataclass(frozen=True)
class OrderBookSnapshot:
    """A snapshot of an order book at a specific point in time.

    Attributes:
        bids: Tuple of bid levels.
        asks: Tuple of ask levels.
        timestamp: Unix timestamp of the snapshot.
        symbol: Trading symbol (e.g., "BTCUSDT").
    """

    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    timestamp: float
    symbol: str

    def __post_init__(self) -> None:
        """Validate and normalize snapshot data."""
        # Convert lists to tuples for bids and asks (frozen dataclass workaround)
        if isinstance(self.bids, list):
            object.__setattr__(self, "bids", tuple(self.bids))
        if isinstance(self.asks, list):
            object.__setattr__(self, "asks", tuple(self.asks))

        # Validate symbol is not empty or whitespace-only
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol must not be empty or whitespace-only")

        # Validate timestamp is non-negative
        if self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")
