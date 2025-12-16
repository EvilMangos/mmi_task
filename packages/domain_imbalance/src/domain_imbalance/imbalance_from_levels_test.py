"""Tests for the imbalance_from_levels helper function.

This function computes total bid/ask volumes from price level lists
and delegates to the core imbalance_ratio function.

Requirements covered:
- R2: Division by zero handling (empty levels)
- R4: All-bid returns 1.0
- R5: All-ask returns -1.0
- R6: Equal total volumes return 0.0
- R7: Helper computes totals from level lists and delegates to core function

Level format: Each level is a tuple of (price, quantity).
Only quantity matters for imbalance calculation, price is used for ordering only.
"""

import pytest

from domain_imbalance.imbalance_from_levels import imbalance_from_levels

# Type alias for clarity in tests
Level = tuple[float, float]  # (price, quantity)


class TestImbalanceFromLevelsEmptyInputs:
    """Test behavior with empty or missing level data."""

    def test_empty_levels_returns_zero(self) -> None:
        """R2, R7: When both bid and ask levels are empty, return 0.0."""
        result = imbalance_from_levels(bids=[], asks=[])
        assert result == pytest.approx(0.0)

    def test_empty_bids_with_asks_returns_negative_one(self) -> None:
        """R5, R7: When only asks exist, ratio should be -1.0."""
        asks: list[Level] = [(100.0, 50.0)]
        result = imbalance_from_levels(bids=[], asks=asks)
        assert result == pytest.approx(-1.0)

    def test_empty_asks_with_bids_returns_positive_one(self) -> None:
        """R4, R7: When only bids exist, ratio should be 1.0."""
        bids: list[Level] = [(99.0, 50.0)]
        result = imbalance_from_levels(bids=bids, asks=[])
        assert result == pytest.approx(1.0)


class TestImbalanceFromLevelsSingleLevel:
    """Test with single price levels."""

    def test_single_bid_level_no_asks(self) -> None:
        """R4, R7: Single bid with no asks returns 1.0."""
        bids: list[Level] = [(100.0, 25.0)]
        result = imbalance_from_levels(bids=bids, asks=[])
        assert result == pytest.approx(1.0)

    def test_single_ask_level_no_bids(self) -> None:
        """R5, R7: Single ask with no bids returns -1.0."""
        asks: list[Level] = [(101.0, 25.0)]
        result = imbalance_from_levels(bids=[], asks=asks)
        assert result == pytest.approx(-1.0)

    def test_single_level_each_equal_quantity(self) -> None:
        """R6, R7: Equal quantities at single levels returns 0.0."""
        bids: list[Level] = [(100.0, 50.0)]
        asks: list[Level] = [(101.0, 50.0)]
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.0)

    def test_single_level_each_unequal_quantity(self) -> None:
        """R1, R7: Unequal quantities compute correct ratio."""
        # bid=30, ask=10 -> (30-10)/(30+10) = 20/40 = 0.5
        bids: list[Level] = [(100.0, 30.0)]
        asks: list[Level] = [(101.0, 10.0)]
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.5)


class TestImbalanceFromLevelsMultipleLevels:
    """Test with multiple price levels."""

    def test_multiple_levels_computes_totals(self) -> None:
        """R1, R7: Multiple levels should sum quantities correctly."""
        # bid total = 10 + 20 + 30 = 60
        # ask total = 15 + 25 = 40
        # ratio = (60 - 40) / (60 + 40) = 20/100 = 0.2
        bids: list[Level] = [
            (100.0, 10.0),
            (99.0, 20.0),
            (98.0, 30.0),
        ]
        asks: list[Level] = [
            (101.0, 15.0),
            (102.0, 25.0),
        ]
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.2)

    def test_multiple_levels_equal_total_volumes(self) -> None:
        """R6, R7: Multiple levels with equal total volumes returns 0.0."""
        # bid total = 10 + 20 + 30 = 60
        # ask total = 25 + 35 = 60
        bids: list[Level] = [
            (100.0, 10.0),
            (99.0, 20.0),
            (98.0, 30.0),
        ]
        asks: list[Level] = [
            (101.0, 25.0),
            (102.0, 35.0),
        ]
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.0)

    def test_ten_levels_each_side(self) -> None:
        """R7: Typical use case with 10 levels on each side (top N=10)."""
        # Create 10 bid levels with quantities 1-10 (total = 55)
        bids: list[Level] = [(100.0 - i, float(i + 1)) for i in range(10)]
        # Create 10 ask levels with quantities 2-11 (total = 65)
        asks: list[Level] = [(101.0 + i, float(i + 2)) for i in range(10)]

        # bid total = 1+2+3+4+5+6+7+8+9+10 = 55
        # ask total = 2+3+4+5+6+7+8+9+10+11 = 65
        # ratio = (55 - 65) / (55 + 65) = -10/120 = -0.0833...
        expected = (55.0 - 65.0) / (55.0 + 65.0)
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(expected)


class TestImbalanceFromLevelsPriceIndependence:
    """Test that price values do not affect the imbalance ratio."""

    def test_only_quantity_matters_not_price(self) -> None:
        """R7: Price values should not affect the imbalance calculation."""
        # Same quantities, different prices
        bids1: list[Level] = [(100.0, 50.0), (99.0, 30.0)]
        asks1: list[Level] = [(101.0, 40.0)]

        bids2: list[Level] = [(50000.0, 50.0), (49999.0, 30.0)]
        asks2: list[Level] = [(50001.0, 40.0)]

        bids3: list[Level] = [(0.001, 50.0), (0.0009, 30.0)]
        asks3: list[Level] = [(0.0011, 40.0)]

        result1 = imbalance_from_levels(bids=bids1, asks=asks1)
        result2 = imbalance_from_levels(bids=bids2, asks=asks2)
        result3 = imbalance_from_levels(bids=bids3, asks=asks3)

        assert result1 == pytest.approx(result2)
        assert result1 == pytest.approx(result3)

    def test_price_ordering_does_not_matter(self) -> None:
        """R7: Order of levels in the list should not affect result."""
        # Same quantities, different order
        bids1: list[Level] = [(100.0, 10.0), (99.0, 20.0), (98.0, 30.0)]
        asks1: list[Level] = [(101.0, 15.0), (102.0, 25.0)]

        # Reversed order
        bids2: list[Level] = [(98.0, 30.0), (99.0, 20.0), (100.0, 10.0)]
        asks2: list[Level] = [(102.0, 25.0), (101.0, 15.0)]

        result1 = imbalance_from_levels(bids=bids1, asks=asks1)
        result2 = imbalance_from_levels(bids=bids2, asks=asks2)

        assert result1 == pytest.approx(result2)


class TestImbalanceFromLevelsZeroQuantities:
    """Test behavior with zero quantity levels."""

    def test_zero_quantity_levels_are_included(self) -> None:
        """Zero quantity levels should be summed (adding 0)."""
        # bid total = 50 + 0 = 50
        # ask total = 50
        bids: list[Level] = [(100.0, 50.0), (99.0, 0.0)]
        asks: list[Level] = [(101.0, 50.0)]
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.0)

    def test_all_zero_quantity_levels(self) -> None:
        """R2: All zero quantity levels should return 0.0."""
        bids: list[Level] = [(100.0, 0.0), (99.0, 0.0)]
        asks: list[Level] = [(101.0, 0.0)]
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.0)


class TestImbalanceFromLevelsFloatPrecision:
    """Test floating point handling in level aggregation."""

    def test_small_quantities_aggregation(self) -> None:
        """Small quantities should aggregate correctly."""
        bids: list[Level] = [(100.0, 0.0001), (99.0, 0.0002), (98.0, 0.0003)]
        asks: list[Level] = [(101.0, 0.0003), (102.0, 0.0003)]
        # bid total = 0.0006, ask total = 0.0006
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.0)

    def test_large_quantities_aggregation(self) -> None:
        """Large quantities should aggregate without overflow."""
        bids: list[Level] = [(100.0, 1e14), (99.0, 1e14)]
        asks: list[Level] = [(101.0, 1e14), (102.0, 1e14)]
        # bid total = 2e14, ask total = 2e14
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(0.0)


class TestImbalanceFromLevelsRealWorldScenarios:
    """Test with realistic order book scenarios."""

    def test_btc_usdt_typical_orderbook_snapshot(self) -> None:
        """Simulate a typical BTC/USDT orderbook snapshot."""
        # Prices around 50000 USDT, quantities in BTC
        bids: list[Level] = [
            (50000.0, 0.5),
            (49999.0, 1.2),
            (49998.0, 0.8),
            (49997.0, 2.1),
            (49996.0, 0.3),
        ]
        asks: list[Level] = [
            (50001.0, 0.4),
            (50002.0, 1.5),
            (50003.0, 0.6),
            (50004.0, 1.8),
            (50005.0, 0.5),
        ]
        # bid total = 0.5 + 1.2 + 0.8 + 2.1 + 0.3 = 4.9
        # ask total = 0.4 + 1.5 + 0.6 + 1.8 + 0.5 = 4.8
        # ratio = (4.9 - 4.8) / (4.9 + 4.8) = 0.1 / 9.7 = 0.0103...
        expected = (4.9 - 4.8) / (4.9 + 4.8)
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_high_imbalance_buy_pressure(self) -> None:
        """Simulate strong buy pressure (many more bids than asks)."""
        bids: list[Level] = [
            (100.0, 100.0),
            (99.0, 150.0),
            (98.0, 200.0),
        ]
        asks: list[Level] = [
            (101.0, 10.0),
            (102.0, 5.0),
        ]
        # bid total = 450, ask total = 15
        # ratio = (450 - 15) / (450 + 15) = 435/465 = 0.935...
        expected = (450.0 - 15.0) / (450.0 + 15.0)
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(expected)
        assert result > 0.9  # Strong positive imbalance

    def test_high_imbalance_sell_pressure(self) -> None:
        """Simulate strong sell pressure (many more asks than bids)."""
        bids: list[Level] = [
            (100.0, 5.0),
            (99.0, 10.0),
        ]
        asks: list[Level] = [
            (101.0, 100.0),
            (102.0, 150.0),
            (103.0, 200.0),
        ]
        # bid total = 15, ask total = 450
        # ratio = (15 - 450) / (15 + 450) = -435/465 = -0.935...
        expected = (15.0 - 450.0) / (15.0 + 450.0)
        result = imbalance_from_levels(bids=bids, asks=asks)
        assert result == pytest.approx(expected)
        assert result < -0.9  # Strong negative imbalance
