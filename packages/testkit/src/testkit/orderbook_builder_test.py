"""Tests for OrderBookBuilder - fluent API for building OrderBookSnapshot test data."""

from decimal import Decimal

import pytest
from domain_orderbook import OrderBookLevel, OrderBookSnapshot

from testkit.orderbook_builder import orderbook_builder


class TestOrderBookBuilderDefaults:
    """Test default values when building without explicit configuration."""

    def test_build_with_defaults(self):
        snapshot = orderbook_builder().build()

        assert snapshot.symbol == "BTCUSDT"
        assert snapshot.timestamp == 0.0
        assert snapshot.bids == ()
        assert snapshot.asks == ()

    def test_build_returns_orderbook_snapshot(self):
        snapshot = orderbook_builder().build()

        assert isinstance(snapshot, OrderBookSnapshot)

    def test_default_bids_are_empty_tuple(self):
        snapshot = orderbook_builder().build()

        assert snapshot.bids == ()
        assert isinstance(snapshot.bids, tuple)

    def test_default_asks_are_empty_tuple(self):
        snapshot = orderbook_builder().build()

        assert snapshot.asks == ()
        assert isinstance(snapshot.asks, tuple)


class TestOrderBookBuilderWithSymbol:
    """Test symbol configuration."""

    def test_with_symbol_sets_symbol(self):
        snapshot = orderbook_builder().with_symbol("DOTUSDT").build()

        assert snapshot.symbol == "DOTUSDT"

    def test_with_symbol_multiple_times_uses_last(self):
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_symbol("DOTUSDT")
            .with_symbol("SOLUSDT")
            .build()
        )

        assert snapshot.symbol == "SOLUSDT"

    def test_with_symbol_empty_string_raises_error(self):
        with pytest.raises(ValueError, match="symbol must not be empty"):
            orderbook_builder().with_symbol("").build()

    def test_with_symbol_special_characters(self):
        snapshot = orderbook_builder().with_symbol("BTC-USDT_TEST").build()

        assert snapshot.symbol == "BTC-USDT_TEST"


class TestOrderBookBuilderWithTimestamp:
    """Test timestamp configuration."""

    def test_with_timestamp_sets_timestamp(self):
        snapshot = orderbook_builder().with_timestamp(1234567890.0).build()

        assert snapshot.timestamp == 1234567890.0

    def test_with_timestamp_integer_value(self):
        snapshot = orderbook_builder().with_timestamp(1234567890).build()

        assert snapshot.timestamp == 1234567890

    def test_with_timestamp_zero(self):
        snapshot = orderbook_builder().with_timestamp(0).build()

        assert snapshot.timestamp == 0

    def test_with_timestamp_negative_raises_error(self):
        with pytest.raises(ValueError, match="timestamp must be non-negative"):
            orderbook_builder().with_timestamp(-100.5).build()

    def test_with_timestamp_fractional_seconds(self):
        snapshot = orderbook_builder().with_timestamp(1234567890.123456).build()

        assert snapshot.timestamp == 1234567890.123456

    def test_with_timestamp_multiple_times_uses_last(self):
        snapshot = (
            orderbook_builder()
            .with_timestamp(100.0)
            .with_timestamp(200.0)
            .with_timestamp(300.0)
            .build()
        )

        assert snapshot.timestamp == 300.0


class TestOrderBookBuilderWithBids:
    """Test bid configuration."""

    def test_with_bids_empty_list(self):
        snapshot = orderbook_builder().with_bids([]).build()

        assert snapshot.bids == ()

    def test_with_bids_single_level(self):
        snapshot = orderbook_builder().with_bids([("100.5", "10.0")]).build()

        assert len(snapshot.bids) == 1
        assert snapshot.bids[0].price == Decimal("100.5")
        assert snapshot.bids[0].qty == Decimal("10.0")

    def test_with_bids_multiple_levels(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100.5", "10.0"), ("100.0", "20.0"), ("99.5", "15.5")])
            .build()
        )

        assert len(snapshot.bids) == 3
        assert snapshot.bids[0].price == Decimal("100.5")
        assert snapshot.bids[0].qty == Decimal("10.0")
        assert snapshot.bids[1].price == Decimal("100.0")
        assert snapshot.bids[1].qty == Decimal("20.0")
        assert snapshot.bids[2].price == Decimal("99.5")
        assert snapshot.bids[2].qty == Decimal("15.5")

    def test_with_bids_preserves_order(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100", "1"), ("200", "2"), ("300", "3")])
            .build()
        )

        prices = [level.price for level in snapshot.bids]
        assert prices == [Decimal("100"), Decimal("200"), Decimal("300")]

    def test_with_bids_converts_to_decimal(self):
        snapshot = orderbook_builder().with_bids([("100.123456", "10.987654")]).build()

        assert isinstance(snapshot.bids[0].price, Decimal)
        assert isinstance(snapshot.bids[0].qty, Decimal)
        assert snapshot.bids[0].price == Decimal("100.123456")
        assert snapshot.bids[0].qty == Decimal("10.987654")

    def test_with_bids_returns_tuple(self):
        snapshot = orderbook_builder().with_bids([("100", "10")]).build()

        assert isinstance(snapshot.bids, tuple)

    def test_with_bids_creates_orderbook_levels(self):
        snapshot = orderbook_builder().with_bids([("100", "10")]).build()

        assert isinstance(snapshot.bids[0], OrderBookLevel)

    def test_with_bids_multiple_times_uses_last(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100", "10")])
            .with_bids([("200", "20")])
            .build()
        )

        assert len(snapshot.bids) == 1
        assert snapshot.bids[0].price == Decimal("200")

    def test_with_bids_with_integer_strings(self):
        snapshot = orderbook_builder().with_bids([("100", "10")]).build()

        assert snapshot.bids[0].price == Decimal("100")
        assert snapshot.bids[0].qty == Decimal("10")

    def test_with_bids_with_scientific_notation(self):
        snapshot = orderbook_builder().with_bids([("1.5e2", "1e1")]).build()

        assert snapshot.bids[0].price == Decimal("1.5e2")
        assert snapshot.bids[0].qty == Decimal("1e1")


class TestOrderBookBuilderWithAsks:
    """Test ask configuration."""

    def test_with_asks_empty_list(self):
        snapshot = orderbook_builder().with_asks([]).build()

        assert snapshot.asks == ()

    def test_with_asks_single_level(self):
        snapshot = orderbook_builder().with_asks([("101.5", "12.0")]).build()

        assert len(snapshot.asks) == 1
        assert snapshot.asks[0].price == Decimal("101.5")
        assert snapshot.asks[0].qty == Decimal("12.0")

    def test_with_asks_multiple_levels(self):
        snapshot = (
            orderbook_builder()
            .with_asks([("101.0", "10.0"), ("101.5", "15.0"), ("102.0", "20.0")])
            .build()
        )

        assert len(snapshot.asks) == 3
        assert snapshot.asks[0].price == Decimal("101.0")
        assert snapshot.asks[1].price == Decimal("101.5")
        assert snapshot.asks[2].price == Decimal("102.0")

    def test_with_asks_preserves_order(self):
        snapshot = (
            orderbook_builder()
            .with_asks([("100", "1"), ("200", "2"), ("300", "3")])
            .build()
        )

        prices = [level.price for level in snapshot.asks]
        assert prices == [Decimal("100"), Decimal("200"), Decimal("300")]

    def test_with_asks_converts_to_decimal(self):
        snapshot = orderbook_builder().with_asks([("101.123456", "11.987654")]).build()

        assert isinstance(snapshot.asks[0].price, Decimal)
        assert isinstance(snapshot.asks[0].qty, Decimal)

    def test_with_asks_returns_tuple(self):
        snapshot = orderbook_builder().with_asks([("101", "10")]).build()

        assert isinstance(snapshot.asks, tuple)

    def test_with_asks_creates_orderbook_levels(self):
        snapshot = orderbook_builder().with_asks([("101", "10")]).build()

        assert isinstance(snapshot.asks[0], OrderBookLevel)

    def test_with_asks_multiple_times_uses_last(self):
        snapshot = (
            orderbook_builder()
            .with_asks([("101", "10")])
            .with_asks([("202", "20")])
            .build()
        )

        assert len(snapshot.asks) == 1
        assert snapshot.asks[0].price == Decimal("202")


class TestOrderBookBuilderWithLevels:
    """Test configuring both bids and asks together."""

    def test_with_levels_sets_both_bids_and_asks(self):
        snapshot = (
            orderbook_builder()
            .with_levels(bids=[("100", "10")], asks=[("101", "11")])
            .build()
        )

        assert len(snapshot.bids) == 1
        assert len(snapshot.asks) == 1
        assert snapshot.bids[0].price == Decimal("100")
        assert snapshot.asks[0].price == Decimal("101")

    def test_with_levels_empty_lists(self):
        snapshot = orderbook_builder().with_levels(bids=[], asks=[]).build()

        assert snapshot.bids == ()
        assert snapshot.asks == ()

    def test_with_levels_only_bids(self):
        snapshot = (
            orderbook_builder().with_levels(bids=[("100", "10")], asks=[]).build()
        )

        assert len(snapshot.bids) == 1
        assert snapshot.asks == ()

    def test_with_levels_only_asks(self):
        snapshot = (
            orderbook_builder().with_levels(bids=[], asks=[("101", "11")]).build()
        )

        assert snapshot.bids == ()
        assert len(snapshot.asks) == 1

    def test_with_levels_multiple_levels_each_side(self):
        snapshot = (
            orderbook_builder()
            .with_levels(
                bids=[("100", "10"), ("99", "20")],
                asks=[("101", "11"), ("102", "22")],
            )
            .build()
        )

        assert len(snapshot.bids) == 2
        assert len(snapshot.asks) == 2


class TestOrderBookBuilderWithSingleBid:
    """Test adding a single bid level."""

    def test_with_single_bid_adds_one_level(self):
        snapshot = orderbook_builder().with_single_bid("100.5", "10.0").build()

        assert len(snapshot.bids) == 1
        assert snapshot.bids[0].price == Decimal("100.5")
        assert snapshot.bids[0].qty == Decimal("10.0")

    def test_with_single_bid_converts_to_decimal(self):
        snapshot = orderbook_builder().with_single_bid("100.5", "10.0").build()

        assert isinstance(snapshot.bids[0].price, Decimal)
        assert isinstance(snapshot.bids[0].qty, Decimal)

    def test_with_single_bid_does_not_affect_asks(self):
        snapshot = orderbook_builder().with_single_bid("100", "10").build()

        assert snapshot.asks == ()

    def test_with_single_bid_after_with_bids_replaces(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100", "10"), ("99", "20")])
            .with_single_bid("200", "30")
            .build()
        )

        assert len(snapshot.bids) == 1
        assert snapshot.bids[0].price == Decimal("200")


class TestOrderBookBuilderWithSingleAsk:
    """Test adding a single ask level."""

    def test_with_single_ask_adds_one_level(self):
        snapshot = orderbook_builder().with_single_ask("101.5", "12.0").build()

        assert len(snapshot.asks) == 1
        assert snapshot.asks[0].price == Decimal("101.5")
        assert snapshot.asks[0].qty == Decimal("12.0")

    def test_with_single_ask_converts_to_decimal(self):
        snapshot = orderbook_builder().with_single_ask("101.5", "12.0").build()

        assert isinstance(snapshot.asks[0].price, Decimal)
        assert isinstance(snapshot.asks[0].qty, Decimal)

    def test_with_single_ask_does_not_affect_bids(self):
        snapshot = orderbook_builder().with_single_ask("101", "11").build()

        assert snapshot.bids == ()

    def test_with_single_ask_after_with_asks_replaces(self):
        snapshot = (
            orderbook_builder()
            .with_asks([("101", "11"), ("102", "22")])
            .with_single_ask("200", "30")
            .build()
        )

        assert len(snapshot.asks) == 1
        assert snapshot.asks[0].price == Decimal("200")


class TestOrderBookBuilderFluentAPI:
    """Test fluent API chaining."""

    def test_chain_all_methods(self):
        snapshot = (
            orderbook_builder()
            .with_symbol("DOTUSDT")
            .with_timestamp(1234567890.5)
            .with_bids([("100", "10"), ("99", "20")])
            .with_asks([("101", "11"), ("102", "22")])
            .build()
        )

        assert snapshot.symbol == "DOTUSDT"
        assert snapshot.timestamp == 1234567890.5
        assert len(snapshot.bids) == 2
        assert len(snapshot.asks) == 2

    def test_chain_returns_builder(self):
        builder = orderbook_builder()

        assert builder.with_symbol("BTCUSDT") is not None
        assert builder.with_timestamp(123) is not None
        assert builder.with_bids([]) is not None
        assert builder.with_asks([]) is not None

    def test_can_build_multiple_times(self):
        builder = orderbook_builder().with_symbol("BTCUSDT").with_timestamp(123)

        snapshot1 = builder.build()
        snapshot2 = builder.build()

        assert snapshot1.symbol == snapshot2.symbol
        assert snapshot1.timestamp == snapshot2.timestamp

    def test_builder_reuse_with_modifications(self):
        builder = orderbook_builder().with_symbol("BTCUSDT")

        snapshot1 = builder.with_timestamp(100).build()
        snapshot2 = builder.with_timestamp(200).build()

        assert snapshot1.timestamp == 100
        assert snapshot2.timestamp == 200
        assert snapshot1.symbol == snapshot2.symbol


class TestOrderBookBuilderComplexScenarios:
    """Test complex real-world scenarios."""

    def test_build_realistic_orderbook(self):
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1704067200.0)
            .with_bids(
                [
                    ("45000.50", "1.5"),
                    ("45000.00", "2.3"),
                    ("44999.50", "0.8"),
                    ("44999.00", "3.1"),
                    ("44998.50", "1.2"),
                ]
            )
            .with_asks(
                [
                    ("45001.00", "1.8"),
                    ("45001.50", "2.1"),
                    ("45002.00", "0.9"),
                    ("45002.50", "3.5"),
                    ("45003.00", "1.4"),
                ]
            )
            .build()
        )

        assert snapshot.symbol == "BTCUSDT"
        assert len(snapshot.bids) == 5
        assert len(snapshot.asks) == 5
        assert snapshot.bids[0].price > snapshot.bids[1].price

    def test_build_empty_orderbook(self):
        snapshot = (
            orderbook_builder()
            .with_symbol("DOTUSDT")
            .with_timestamp(1234567890.0)
            .build()
        )

        assert snapshot.symbol == "DOTUSDT"
        assert snapshot.bids == ()
        assert snapshot.asks == ()

    def test_build_orderbook_with_only_bids(self):
        snapshot = (
            orderbook_builder()
            .with_symbol("SOLUSDT")
            .with_bids([("100", "10"), ("99", "20")])
            .build()
        )

        assert len(snapshot.bids) == 2
        assert snapshot.asks == ()

    def test_build_orderbook_with_only_asks(self):
        snapshot = (
            orderbook_builder()
            .with_symbol("SOLUSDT")
            .with_asks([("101", "11"), ("102", "22")])
            .build()
        )

        assert snapshot.bids == ()
        assert len(snapshot.asks) == 2

    def test_build_with_very_precise_decimals(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100.12345678", "10.87654321")])
            .with_asks([("101.98765432", "11.23456789")])
            .build()
        )

        assert snapshot.bids[0].price == Decimal("100.12345678")
        assert snapshot.bids[0].qty == Decimal("10.87654321")
        assert snapshot.asks[0].price == Decimal("101.98765432")
        assert snapshot.asks[0].qty == Decimal("11.23456789")

    def test_build_with_large_quantities(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100", "1000000.0")])
            .with_asks([("101", "2000000.0")])
            .build()
        )

        assert snapshot.bids[0].qty == Decimal("1000000.0")
        assert snapshot.asks[0].qty == Decimal("2000000.0")

    def test_build_with_small_prices(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("0.00000001", "1000000")])
            .with_asks([("0.00000002", "2000000")])
            .build()
        )

        assert snapshot.bids[0].price == Decimal("0.00000001")
        assert snapshot.asks[0].price == Decimal("0.00000002")


class TestOrderBookBuilderEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_build_with_zero_prices(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("0", "10")])
            .with_asks([("0", "11")])
            .build()
        )

        assert snapshot.bids[0].price == Decimal("0")
        assert snapshot.asks[0].price == Decimal("0")

    def test_build_with_zero_quantities(self):
        snapshot = (
            orderbook_builder()
            .with_bids([("100", "0")])
            .with_asks([("101", "0")])
            .build()
        )

        assert snapshot.bids[0].qty == Decimal("0")
        assert snapshot.asks[0].qty == Decimal("0")

    def test_build_with_many_levels(self):
        many_bids = [(str(100 - i), str(i + 1)) for i in range(100)]
        many_asks = [(str(101 + i), str(i + 1)) for i in range(100)]

        snapshot = orderbook_builder().with_bids(many_bids).with_asks(many_asks).build()

        assert len(snapshot.bids) == 100
        assert len(snapshot.asks) == 100

    def test_build_preserves_decimal_precision(self):
        snapshot = orderbook_builder().with_bids([("100.10", "10.01")]).build()

        # Decimal should preserve trailing zeros in string representation
        assert snapshot.bids[0].price == Decimal("100.10")
        assert snapshot.bids[0].qty == Decimal("10.01")

    def test_function_returns_new_builder_each_time(self):
        builder1 = orderbook_builder()
        builder2 = orderbook_builder()

        # Each call should return a fresh builder
        builder1.with_symbol("ETHUSDT")  # Modify builder1 with non-default symbol
        snapshot2 = builder2.build()

        # builder2 should still have default symbol (unaffected by builder1 modification)
        assert snapshot2.symbol == "BTCUSDT"
