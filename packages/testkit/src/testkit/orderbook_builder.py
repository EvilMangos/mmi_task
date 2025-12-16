"""Fluent builder for OrderBookSnapshot test data."""

from decimal import Decimal

from domain_orderbook import OrderBookLevel, OrderBookSnapshot


class OrderBookBuilder:
    """Fluent API for building OrderBookSnapshot instances in tests."""

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._symbol = "BTCUSDT"
        self._timestamp: float = 0.0
        self._bids: tuple[OrderBookLevel, ...] = ()
        self._asks: tuple[OrderBookLevel, ...] = ()

    def with_symbol(self, symbol: str) -> "OrderBookBuilder":
        """Set the symbol.

        Args:
            symbol: The trading pair symbol.

        Returns:
            Self for chaining.
        """
        self._symbol = symbol
        return self

    def with_timestamp(self, timestamp: float) -> "OrderBookBuilder":
        """Set the timestamp.

        Args:
            timestamp: Unix timestamp (seconds since epoch).

        Returns:
            Self for chaining.
        """
        self._timestamp = timestamp
        return self

    def with_bids(self, bids: list[tuple[str, str]]) -> "OrderBookBuilder":
        """Set the bid levels.

        Args:
            bids: List of (price, qty) tuples as strings.

        Returns:
            Self for chaining.
        """
        self._bids = tuple(
            OrderBookLevel(price=Decimal(price), qty=Decimal(qty))
            for price, qty in bids
        )
        return self

    def with_asks(self, asks: list[tuple[str, str]]) -> "OrderBookBuilder":
        """Set the ask levels.

        Args:
            asks: List of (price, qty) tuples as strings.

        Returns:
            Self for chaining.
        """
        self._asks = tuple(
            OrderBookLevel(price=Decimal(price), qty=Decimal(qty))
            for price, qty in asks
        )
        return self

    def with_levels(
        self, bids: list[tuple[str, str]], asks: list[tuple[str, str]]
    ) -> "OrderBookBuilder":
        """Set both bids and asks at once.

        Args:
            bids: List of (price, qty) tuples as strings.
            asks: List of (price, qty) tuples as strings.

        Returns:
            Self for chaining.
        """
        self.with_bids(bids)
        self.with_asks(asks)
        return self

    def with_single_bid(self, price: str, qty: str) -> "OrderBookBuilder":
        """Set a single bid level.

        Args:
            price: Bid price as string.
            qty: Bid quantity as string.

        Returns:
            Self for chaining.
        """
        self._bids = (OrderBookLevel(price=Decimal(price), qty=Decimal(qty)),)
        return self

    def with_single_ask(self, price: str, qty: str) -> "OrderBookBuilder":
        """Set a single ask level.

        Args:
            price: Ask price as string.
            qty: Ask quantity as string.

        Returns:
            Self for chaining.
        """
        self._asks = (OrderBookLevel(price=Decimal(price), qty=Decimal(qty)),)
        return self

    def build(self) -> OrderBookSnapshot:
        """Build the OrderBookSnapshot.

        Returns:
            Configured OrderBookSnapshot instance.
        """
        return OrderBookSnapshot(
            symbol=self._symbol,
            timestamp=self._timestamp,
            bids=self._bids,
            asks=self._asks,
        )


def orderbook_builder() -> OrderBookBuilder:
    """Create a new OrderBookBuilder instance.

    Returns:
        Fresh builder with default values.
    """
    return OrderBookBuilder()
