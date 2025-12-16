"""Tests for order book helper functions.

Helper functions provide operations for normalizing, selecting, and
aggregating order book levels.
"""

from decimal import Decimal

import pytest

from domain_orderbook.level import OrderBookLevel
from domain_orderbook.helpers import (
    normalize_bids,
    normalize_asks,
    top_n_bids,
    top_n_asks,
    sum_volume,
)


def _make_level(price: str, qty: str) -> OrderBookLevel:
    """Helper to create OrderBookLevel from string values."""
    return OrderBookLevel(price=Decimal(price), qty=Decimal(qty))


class TestNormalizeBids:
    """Tests for normalize_bids function.

    normalize_bids sorts levels by price descending (highest price first).
    """

    def test_empty_input_returns_empty_tuple(self) -> None:
        result = normalize_bids([])

        assert result == ()
        assert isinstance(result, tuple)

    def test_single_level_returns_as_tuple(self) -> None:
        level = _make_level("100", "10")

        result = normalize_bids([level])

        assert result == (level,)
        assert isinstance(result, tuple)

    def test_sorts_by_price_descending(self) -> None:
        low = _make_level("99", "10")
        mid = _make_level("100", "20")
        high = _make_level("101", "30")

        result = normalize_bids([low, high, mid])

        assert result == (high, mid, low)

    def test_already_sorted_descending_unchanged(self) -> None:
        high = _make_level("101", "30")
        mid = _make_level("100", "20")
        low = _make_level("99", "10")

        result = normalize_bids([high, mid, low])

        assert result == (high, mid, low)

    def test_duplicate_prices_maintain_stable_order(self) -> None:
        level1 = _make_level("100", "10")
        level2 = _make_level("100", "20")
        level3 = _make_level("100", "30")

        result = normalize_bids([level1, level2, level3])

        # All three should be present (stable sort preserves input order for equal keys)
        assert len(result) == 3
        assert all(level.price == Decimal("100") for level in result)

    def test_accepts_tuple_input(self) -> None:
        low = _make_level("99", "10")
        high = _make_level("101", "30")

        result = normalize_bids((low, high))

        assert result == (high, low)

    def test_handles_many_levels(self) -> None:
        levels = [_make_level(str(i), "10") for i in range(100)]

        result = normalize_bids(levels)

        assert len(result) == 100
        # Should be sorted descending
        prices = [level.price for level in result]
        assert prices == sorted(prices, reverse=True)


class TestNormalizeAsks:
    """Tests for normalize_asks function.

    normalize_asks sorts levels by price ascending (lowest price first).
    """

    def test_empty_input_returns_empty_tuple(self) -> None:
        result = normalize_asks([])

        assert result == ()
        assert isinstance(result, tuple)

    def test_single_level_returns_as_tuple(self) -> None:
        level = _make_level("100", "10")

        result = normalize_asks([level])

        assert result == (level,)
        assert isinstance(result, tuple)

    def test_sorts_by_price_ascending(self) -> None:
        low = _make_level("99", "10")
        mid = _make_level("100", "20")
        high = _make_level("101", "30")

        result = normalize_asks([high, low, mid])

        assert result == (low, mid, high)

    def test_already_sorted_ascending_unchanged(self) -> None:
        low = _make_level("99", "10")
        mid = _make_level("100", "20")
        high = _make_level("101", "30")

        result = normalize_asks([low, mid, high])

        assert result == (low, mid, high)

    def test_duplicate_prices_maintain_stable_order(self) -> None:
        level1 = _make_level("100", "10")
        level2 = _make_level("100", "20")
        level3 = _make_level("100", "30")

        result = normalize_asks([level1, level2, level3])

        assert len(result) == 3
        assert all(level.price == Decimal("100") for level in result)

    def test_accepts_tuple_input(self) -> None:
        low = _make_level("99", "10")
        high = _make_level("101", "30")

        result = normalize_asks((high, low))

        assert result == (low, high)

    def test_handles_many_levels(self) -> None:
        levels = [_make_level(str(i), "10") for i in range(100, 0, -1)]

        result = normalize_asks(levels)

        assert len(result) == 100
        prices = [level.price for level in result]
        assert prices == sorted(prices)


class TestTopNBids:
    """Tests for top_n_bids function.

    top_n_bids returns the N highest-priced levels, sorted descending.
    """

    def test_empty_input_returns_empty_tuple(self) -> None:
        result = top_n_bids([], 5)

        assert result == ()
        assert isinstance(result, tuple)

    def test_n_zero_returns_empty_tuple(self) -> None:
        levels = [_make_level("100", "10"), _make_level("99", "20")]

        result = top_n_bids(levels, 0)

        assert result == ()

    def test_returns_n_highest_priced_levels(self) -> None:
        low = _make_level("98", "10")
        mid = _make_level("99", "20")
        high = _make_level("100", "30")

        result = top_n_bids([low, mid, high], 2)

        assert result == (high, mid)

    def test_result_sorted_descending(self) -> None:
        levels = [
            _make_level("95", "10"),
            _make_level("100", "20"),
            _make_level("97", "30"),
            _make_level("99", "40"),
        ]

        result = top_n_bids(levels, 3)

        prices = [level.price for level in result]
        assert prices == sorted(prices, reverse=True)
        assert prices == [Decimal("100"), Decimal("99"), Decimal("97")]

    def test_n_greater_than_length_returns_all(self) -> None:
        low = _make_level("99", "10")
        high = _make_level("100", "20")

        result = top_n_bids([low, high], 10)

        assert len(result) == 2
        assert result == (high, low)

    def test_n_equal_to_length_returns_all(self) -> None:
        low = _make_level("99", "10")
        high = _make_level("100", "20")

        result = top_n_bids([low, high], 2)

        assert len(result) == 2
        assert result == (high, low)

    def test_negative_n_raises_value_error(self) -> None:
        levels = [_make_level("100", "10")]

        with pytest.raises(ValueError, match="n"):
            top_n_bids(levels, -1)

    def test_accepts_tuple_input(self) -> None:
        low = _make_level("99", "10")
        high = _make_level("100", "20")

        result = top_n_bids((low, high), 1)

        assert result == (high,)

    def test_handles_single_element(self) -> None:
        level = _make_level("100", "10")

        result = top_n_bids([level], 1)

        assert result == (level,)

    def test_handles_many_levels(self) -> None:
        levels = [_make_level(str(i), "10") for i in range(1, 101)]

        result = top_n_bids(levels, 10)

        assert len(result) == 10
        prices = [level.price for level in result]
        assert prices == [Decimal(str(i)) for i in range(100, 90, -1)]


class TestTopNAsks:
    """Tests for top_n_asks function.

    top_n_asks returns the N lowest-priced levels, sorted ascending.
    """

    def test_empty_input_returns_empty_tuple(self) -> None:
        result = top_n_asks([], 5)

        assert result == ()
        assert isinstance(result, tuple)

    def test_n_zero_returns_empty_tuple(self) -> None:
        levels = [_make_level("100", "10"), _make_level("101", "20")]

        result = top_n_asks(levels, 0)

        assert result == ()

    def test_returns_n_lowest_priced_levels(self) -> None:
        low = _make_level("100", "10")
        mid = _make_level("101", "20")
        high = _make_level("102", "30")

        result = top_n_asks([high, low, mid], 2)

        assert result == (low, mid)

    def test_result_sorted_ascending(self) -> None:
        levels = [
            _make_level("105", "10"),
            _make_level("100", "20"),
            _make_level("103", "30"),
            _make_level("101", "40"),
        ]

        result = top_n_asks(levels, 3)

        prices = [level.price for level in result]
        assert prices == sorted(prices)
        assert prices == [Decimal("100"), Decimal("101"), Decimal("103")]

    def test_n_greater_than_length_returns_all(self) -> None:
        low = _make_level("100", "10")
        high = _make_level("101", "20")

        result = top_n_asks([high, low], 10)

        assert len(result) == 2
        assert result == (low, high)

    def test_n_equal_to_length_returns_all(self) -> None:
        low = _make_level("100", "10")
        high = _make_level("101", "20")

        result = top_n_asks([high, low], 2)

        assert len(result) == 2
        assert result == (low, high)

    def test_negative_n_raises_value_error(self) -> None:
        levels = [_make_level("100", "10")]

        with pytest.raises(ValueError, match="n"):
            top_n_asks(levels, -1)

    def test_accepts_tuple_input(self) -> None:
        low = _make_level("100", "10")
        high = _make_level("101", "20")

        result = top_n_asks((high, low), 1)

        assert result == (low,)

    def test_handles_single_element(self) -> None:
        level = _make_level("100", "10")

        result = top_n_asks([level], 1)

        assert result == (level,)

    def test_handles_many_levels(self) -> None:
        levels = [_make_level(str(i), "10") for i in range(100, 0, -1)]

        result = top_n_asks(levels, 10)

        assert len(result) == 10
        prices = [level.price for level in result]
        assert prices == [Decimal(str(i)) for i in range(1, 11)]


class TestSumVolume:
    """Tests for sum_volume function.

    sum_volume returns the sum of all qty values in the given levels.
    """

    def test_empty_input_returns_zero(self) -> None:
        result = sum_volume([])

        assert result == Decimal("0")

    def test_single_level_returns_its_qty(self) -> None:
        level = _make_level("100", "25.5")

        result = sum_volume([level])

        assert result == Decimal("25.5")

    def test_sums_multiple_levels(self) -> None:
        levels = [
            _make_level("100", "10"),
            _make_level("101", "20"),
            _make_level("102", "30"),
        ]

        result = sum_volume(levels)

        assert result == Decimal("60")

    def test_preserves_decimal_precision(self) -> None:
        levels = [
            _make_level("100", "0.123456789"),
            _make_level("101", "0.987654321"),
        ]

        result = sum_volume(levels)

        assert result == Decimal("1.111111110")

    def test_handles_zero_quantities(self) -> None:
        levels = [
            _make_level("100", "0"),
            _make_level("101", "10"),
            _make_level("102", "0"),
        ]

        result = sum_volume(levels)

        assert result == Decimal("10")

    def test_handles_all_zero_quantities(self) -> None:
        levels = [
            _make_level("100", "0"),
            _make_level("101", "0"),
        ]

        result = sum_volume(levels)

        assert result == Decimal("0")

    def test_accepts_tuple_input(self) -> None:
        levels = (
            _make_level("100", "10"),
            _make_level("101", "20"),
        )

        result = sum_volume(levels)

        assert result == Decimal("30")

    def test_handles_large_volumes(self) -> None:
        levels = [
            _make_level("100", "999999999.999999999"),
            _make_level("101", "999999999.999999999"),
        ]

        result = sum_volume(levels)

        assert result == Decimal("1999999999.999999998")

    def test_handles_small_volumes(self) -> None:
        levels = [
            _make_level("100", "0.000000001"),
            _make_level("101", "0.000000002"),
        ]

        result = sum_volume(levels)

        assert result == Decimal("0.000000003")

    def test_handles_many_levels(self) -> None:
        levels = [_make_level("100", "1") for _ in range(100)]

        result = sum_volume(levels)

        assert result == Decimal("100")
