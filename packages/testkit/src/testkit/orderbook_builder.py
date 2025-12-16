"""Fluent builder for OrderBookSnapshot test data."""

from __future__ import annotations

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

    def with_symbol(self, symbol: str) -> OrderBookBuilder:
        """Set the symbol.

        Args:
            symbol: The trading pair symbol.

        Returns:
            Self for chaining.
        """
        self._symbol = symbol
        return self

    def with_timestamp(self, timestamp: float) -> OrderBookBuilder:
        """Set the timestamp.

        Args:
            timestamp: Unix timestamp (seconds since epoch).

        Returns:
            Self for chaining.
        """
        self._timestamp = timestamp
        return self

    def with_bids(self, bids: list[tuple[str, str]]) -> OrderBookBuilder:
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

    def with_asks(self, asks: list[tuple[str, str]]) -> OrderBookBuilder:
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
    ) -> OrderBookBuilder:
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

    def with_single_bid(self, price: str, qty: str) -> OrderBookBuilder:
        """Set a single bid level.

        Args:
            price: Bid price as string.
            qty: Bid quantity as string.

        Returns:
            Self for chaining.
        """
        self._bids = (OrderBookLevel(price=Decimal(price), qty=Decimal(qty)),)
        return self

    def with_single_ask(self, price: str, qty: str) -> OrderBookBuilder:
        """Set a single ask level.

        Args:
            price: Ask price as string.
            qty: Ask quantity as string.

        Returns:
            Self for chaining.
        """
        self._asks = (OrderBookLevel(price=Decimal(price), qty=Decimal(qty)),)
        return self

    def with_imbalance_ratio(
        self, ratio: float, total_volume: float = 10.0
    ) -> OrderBookBuilder:
        """Configure bids and asks to achieve a target imbalance ratio.

        Creates a single bid and single ask level with volumes calculated to
        produce the exact specified ratio.

        Formula: ratio = (bid_volume - ask_volume) / (bid_volume + ask_volume)

        Args:
            ratio: Target imbalance ratio in range [-1.0, 1.0].
                   Positive = more bid volume, negative = more ask volume.
            total_volume: Total volume (bid + ask). Defaults to 10.0.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If ratio is outside [-1.0, 1.0] range.

        Example:
            # ratio = 0.5 means bid_vol=7.5, ask_vol=2.5 (with default total=10)
            snapshot = orderbook_builder().with_imbalance_ratio(0.5).build()
        """
        if not -1.0 <= ratio <= 1.0:
            raise ValueError(f"ratio must be between -1.0 and 1.0, got {ratio}")

        # Derive bid and ask volumes from ratio and total_volume
        # ratio = (B - A) / (B + A), where B + A = total_volume
        # ratio * total = B - A
        # B = (total + ratio * total) / 2 = total * (1 + ratio) / 2
        # A = total - B = total * (1 - ratio) / 2
        bid_volume = total_volume * (1 + ratio) / 2
        ask_volume = total_volume * (1 - ratio) / 2

        self._bids = (
            OrderBookLevel(price=Decimal("100.00"), qty=Decimal(str(bid_volume))),
        )
        self._asks = (
            OrderBookLevel(price=Decimal("100.01"), qty=Decimal(str(ask_volume))),
        )
        return self

    def with_balanced_book(self, volume_per_side: float = 5.0) -> OrderBookBuilder:
        """Configure a balanced orderbook with ratio = 0.0.

        Args:
            volume_per_side: Volume for both bid and ask sides. Defaults to 5.0.

        Returns:
            Self for chaining.
        """
        return self.with_imbalance_ratio(0.0, total_volume=volume_per_side * 2)

    def with_high_bid_imbalance(
        self, ratio: float = 0.6, total_volume: float = 10.0
    ) -> OrderBookBuilder:
        """Configure a snapshot with high bid-side imbalance (ratio > 0).

        Convenience method for tests that need an imbalance above typical thresholds.

        Args:
            ratio: Target ratio, must be positive. Defaults to 0.6.
            total_volume: Total volume. Defaults to 10.0.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If ratio is not positive.
        """
        if ratio <= 0:
            raise ValueError(f"ratio must be positive for bid imbalance, got {ratio}")
        return self.with_imbalance_ratio(ratio, total_volume)

    def with_high_ask_imbalance(
        self, ratio: float = -0.6, total_volume: float = 10.0
    ) -> OrderBookBuilder:
        """Configure a snapshot with high ask-side imbalance (ratio < 0).

        Convenience method for tests that need a negative imbalance.

        Args:
            ratio: Target ratio, must be negative. Defaults to -0.6.
            total_volume: Total volume. Defaults to 10.0.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If ratio is not negative.
        """
        if ratio >= 0:
            raise ValueError(f"ratio must be negative for ask imbalance, got {ratio}")
        return self.with_imbalance_ratio(ratio, total_volume)

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
