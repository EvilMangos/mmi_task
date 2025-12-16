"""Tests for OrderBookLevel dataclass.

OrderBookLevel is an immutable frozen dataclass representing a single
price level in an order book with price and quantity fields.
"""

from decimal import Decimal

import pytest

from domain_orderbook.level import OrderBookLevel


class TestOrderBookLevelConstruction:
    """Tests for valid OrderBookLevel construction."""

    def test_creates_level_with_valid_price_and_qty(self) -> None:
        level = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("1.5"))

        assert level.price == Decimal("100.50")
        assert level.qty == Decimal("1.5")

    def test_creates_level_with_zero_price(self) -> None:
        level = OrderBookLevel(price=Decimal("0"), qty=Decimal("10"))

        assert level.price == Decimal("0")
        assert level.qty == Decimal("10")

    def test_creates_level_with_zero_qty(self) -> None:
        level = OrderBookLevel(price=Decimal("50.00"), qty=Decimal("0"))

        assert level.price == Decimal("50.00")
        assert level.qty == Decimal("0")

    def test_creates_level_with_both_zero(self) -> None:
        level = OrderBookLevel(price=Decimal("0"), qty=Decimal("0"))

        assert level.price == Decimal("0")
        assert level.qty == Decimal("0")

    def test_creates_level_with_large_values(self) -> None:
        large_price = Decimal("999999999.999999999")
        large_qty = Decimal("1000000000.123456789")

        level = OrderBookLevel(price=large_price, qty=large_qty)

        assert level.price == large_price
        assert level.qty == large_qty

    def test_creates_level_with_small_values(self) -> None:
        small_price = Decimal("0.00000001")
        small_qty = Decimal("0.00000001")

        level = OrderBookLevel(price=small_price, qty=small_qty)

        assert level.price == small_price
        assert level.qty == small_qty


class TestOrderBookLevelValidation:
    """Tests for OrderBookLevel input validation."""

    def test_rejects_negative_price(self) -> None:
        with pytest.raises(ValueError, match="price"):
            OrderBookLevel(price=Decimal("-1"), qty=Decimal("10"))

    def test_rejects_negative_qty(self) -> None:
        with pytest.raises(ValueError, match="qty"):
            OrderBookLevel(price=Decimal("100"), qty=Decimal("-5"))

    def test_rejects_both_negative(self) -> None:
        with pytest.raises(ValueError):
            OrderBookLevel(price=Decimal("-100"), qty=Decimal("-5"))

    def test_rejects_nan_price(self) -> None:
        nan_decimal = Decimal("NaN")

        with pytest.raises(ValueError, match="price"):
            OrderBookLevel(price=nan_decimal, qty=Decimal("10"))

    def test_rejects_nan_qty(self) -> None:
        nan_decimal = Decimal("NaN")

        with pytest.raises(ValueError, match="qty"):
            OrderBookLevel(price=Decimal("100"), qty=nan_decimal)

    def test_rejects_positive_infinity_price(self) -> None:
        inf_decimal = Decimal("Infinity")

        with pytest.raises(ValueError, match="price"):
            OrderBookLevel(price=inf_decimal, qty=Decimal("10"))

    def test_rejects_negative_infinity_price(self) -> None:
        neg_inf_decimal = Decimal("-Infinity")

        with pytest.raises(ValueError, match="price"):
            OrderBookLevel(price=neg_inf_decimal, qty=Decimal("10"))

    def test_rejects_positive_infinity_qty(self) -> None:
        inf_decimal = Decimal("Infinity")

        with pytest.raises(ValueError, match="qty"):
            OrderBookLevel(price=Decimal("100"), qty=inf_decimal)

    def test_rejects_negative_infinity_qty(self) -> None:
        neg_inf_decimal = Decimal("-Infinity")

        with pytest.raises(ValueError, match="qty"):
            OrderBookLevel(price=Decimal("100"), qty=neg_inf_decimal)


class TestOrderBookLevelImmutability:
    """Tests for OrderBookLevel immutability (frozen dataclass)."""

    def test_cannot_modify_price(self) -> None:
        level = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))

        with pytest.raises(AttributeError):
            level.price = Decimal("200")  # type: ignore[misc]

    def test_cannot_modify_qty(self) -> None:
        level = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))

        with pytest.raises(AttributeError):
            level.qty = Decimal("20")  # type: ignore[misc]


class TestOrderBookLevelEquality:
    """Tests for OrderBookLevel equality comparison."""

    def test_equal_levels_are_equal(self) -> None:
        level1 = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("5.25"))
        level2 = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("5.25"))

        assert level1 == level2

    def test_different_prices_are_not_equal(self) -> None:
        level1 = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("5.25"))
        level2 = OrderBookLevel(price=Decimal("100.51"), qty=Decimal("5.25"))

        assert level1 != level2

    def test_different_quantities_are_not_equal(self) -> None:
        level1 = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("5.25"))
        level2 = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("5.26"))

        assert level1 != level2

    def test_decimal_representation_matters_for_equality(self) -> None:
        # Decimal("100.5") and Decimal("100.50") are equal in value
        level1 = OrderBookLevel(price=Decimal("100.5"), qty=Decimal("5"))
        level2 = OrderBookLevel(price=Decimal("100.50"), qty=Decimal("5.0"))

        # These should be equal as Decimal equality is value-based
        assert level1 == level2


class TestOrderBookLevelHashability:
    """Tests for OrderBookLevel hashability (usable in sets/dicts)."""

    def test_level_is_hashable(self) -> None:
        level = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))

        # Should not raise
        hash_value = hash(level)
        assert isinstance(hash_value, int)

    def test_equal_levels_have_same_hash(self) -> None:
        level1 = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))
        level2 = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))

        assert hash(level1) == hash(level2)

    def test_level_can_be_added_to_set(self) -> None:
        level1 = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))
        level2 = OrderBookLevel(price=Decimal("200"), qty=Decimal("20"))
        level3 = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))  # duplicate

        level_set = {level1, level2, level3}

        assert len(level_set) == 2
        assert level1 in level_set
        assert level2 in level_set

    def test_level_can_be_dict_key(self) -> None:
        level = OrderBookLevel(price=Decimal("100"), qty=Decimal("10"))

        level_dict = {level: "test_value"}

        assert level_dict[level] == "test_value"
