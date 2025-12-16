"""Tests for OrderBookSnapshot dataclass.

OrderBookSnapshot is an immutable frozen dataclass representing a point-in-time
snapshot of an order book with bids, asks, timestamp, and symbol.
"""

import pytest

from domain_orderbook.snapshot import OrderBookSnapshot

# make_level fixture is provided by conftest.py


class TestOrderBookSnapshotConstruction:
    """Tests for valid OrderBookSnapshot construction."""

    def test_creates_snapshot_with_valid_data(self, make_level) -> None:
        bids = (make_level("100", "10"), make_level("99", "20"))
        asks = (make_level("101", "15"), make_level("102", "25"))

        snapshot = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=1234567890.123,
            symbol="BTCUSDT",
        )

        assert snapshot.bids == bids
        assert snapshot.asks == asks
        assert snapshot.timestamp == 1234567890.123
        assert snapshot.symbol == "BTCUSDT"

    def test_creates_snapshot_with_empty_bids(self, make_level) -> None:
        asks = (make_level("101", "15"),)

        snapshot = OrderBookSnapshot(
            bids=(),
            asks=asks,
            timestamp=1000.0,
            symbol="ETHUSDT",
        )

        assert snapshot.bids == ()
        assert snapshot.asks == asks

    def test_creates_snapshot_with_empty_asks(self, make_level) -> None:
        bids = (make_level("100", "10"),)

        snapshot = OrderBookSnapshot(
            bids=bids,
            asks=(),
            timestamp=1000.0,
            symbol="ETHUSDT",
        )

        assert snapshot.bids == bids
        assert snapshot.asks == ()

    def test_creates_snapshot_with_both_empty(self) -> None:
        snapshot = OrderBookSnapshot(
            bids=(),
            asks=(),
            timestamp=1000.0,
            symbol="DOTUSDT",
        )

        assert snapshot.bids == ()
        assert snapshot.asks == ()

    def test_creates_snapshot_with_zero_timestamp(self) -> None:
        snapshot = OrderBookSnapshot(
            bids=(),
            asks=(),
            timestamp=0.0,
            symbol="SOLUSDT",
        )

        assert snapshot.timestamp == 0.0

    def test_creates_snapshot_with_large_timestamp(self) -> None:
        large_timestamp = 9999999999.999999

        snapshot = OrderBookSnapshot(
            bids=(),
            asks=(),
            timestamp=large_timestamp,
            symbol="BTCUSDT",
        )

        assert snapshot.timestamp == large_timestamp


class TestOrderBookSnapshotValidation:
    """Tests for OrderBookSnapshot input validation."""

    def test_rejects_empty_symbol(self) -> None:
        with pytest.raises(ValueError, match="symbol"):
            OrderBookSnapshot(
                bids=(),
                asks=(),
                timestamp=1000.0,
                symbol="",
            )

    def test_rejects_whitespace_only_symbol(self) -> None:
        with pytest.raises(ValueError, match="symbol"):
            OrderBookSnapshot(
                bids=(),
                asks=(),
                timestamp=1000.0,
                symbol="   ",
            )

    def test_rejects_negative_timestamp(self) -> None:
        with pytest.raises(ValueError, match="timestamp"):
            OrderBookSnapshot(
                bids=(),
                asks=(),
                timestamp=-1.0,
                symbol="BTCUSDT",
            )

    def test_rejects_very_negative_timestamp(self) -> None:
        with pytest.raises(ValueError, match="timestamp"):
            OrderBookSnapshot(
                bids=(),
                asks=(),
                timestamp=-999999999.0,
                symbol="BTCUSDT",
            )


class TestOrderBookSnapshotListConversion:
    """Tests for OrderBookSnapshot list-to-tuple conversion."""

    def test_converts_bids_list_to_tuple(self, make_level) -> None:
        bids_list = [make_level("100", "10"), make_level("99", "20")]

        snapshot = OrderBookSnapshot(
            bids=bids_list,  # type: ignore[arg-type]
            asks=(),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert isinstance(snapshot.bids, tuple)
        assert snapshot.bids == tuple(bids_list)

    def test_converts_asks_list_to_tuple(self, make_level) -> None:
        asks_list = [make_level("101", "15"), make_level("102", "25")]

        snapshot = OrderBookSnapshot(
            bids=(),
            asks=asks_list,  # type: ignore[arg-type]
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert isinstance(snapshot.asks, tuple)
        assert snapshot.asks == tuple(asks_list)

    def test_converts_both_lists_to_tuples(self, make_level) -> None:
        bids_list = [make_level("100", "10")]
        asks_list = [make_level("101", "15")]

        snapshot = OrderBookSnapshot(
            bids=bids_list,  # type: ignore[arg-type]
            asks=asks_list,  # type: ignore[arg-type]
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert isinstance(snapshot.bids, tuple)
        assert isinstance(snapshot.asks, tuple)

    def test_preserves_tuples_as_tuples(self, make_level) -> None:
        bids_tuple = (make_level("100", "10"),)
        asks_tuple = (make_level("101", "15"),)

        snapshot = OrderBookSnapshot(
            bids=bids_tuple,
            asks=asks_tuple,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert snapshot.bids is bids_tuple or snapshot.bids == bids_tuple
        assert snapshot.asks is asks_tuple or snapshot.asks == asks_tuple


class TestOrderBookSnapshotImmutability:
    """Tests for OrderBookSnapshot immutability (frozen dataclass)."""

    def test_cannot_modify_bids(self, make_level) -> None:
        snapshot = OrderBookSnapshot(
            bids=(make_level("100", "10"),),
            asks=(),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        with pytest.raises(AttributeError):
            snapshot.bids = ()  # type: ignore[misc]

    def test_cannot_modify_asks(self, make_level) -> None:
        snapshot = OrderBookSnapshot(
            bids=(),
            asks=(make_level("101", "15"),),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        with pytest.raises(AttributeError):
            snapshot.asks = ()  # type: ignore[misc]

    def test_cannot_modify_timestamp(self) -> None:
        snapshot = OrderBookSnapshot(
            bids=(),
            asks=(),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        with pytest.raises(AttributeError):
            snapshot.timestamp = 2000.0  # type: ignore[misc]

    def test_cannot_modify_symbol(self) -> None:
        snapshot = OrderBookSnapshot(
            bids=(),
            asks=(),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        with pytest.raises(AttributeError):
            snapshot.symbol = "ETHUSDT"  # type: ignore[misc]


class TestOrderBookSnapshotEquality:
    """Tests for OrderBookSnapshot equality comparison."""

    def test_equal_snapshots_are_equal(self, make_level) -> None:
        bids = (make_level("100", "10"),)
        asks = (make_level("101", "15"),)

        snapshot1 = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )
        snapshot2 = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert snapshot1 == snapshot2

    def test_different_bids_are_not_equal(self, make_level) -> None:
        asks = (make_level("101", "15"),)

        snapshot1 = OrderBookSnapshot(
            bids=(make_level("100", "10"),),
            asks=asks,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )
        snapshot2 = OrderBookSnapshot(
            bids=(make_level("99", "10"),),
            asks=asks,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert snapshot1 != snapshot2

    def test_different_asks_are_not_equal(self, make_level) -> None:
        bids = (make_level("100", "10"),)

        snapshot1 = OrderBookSnapshot(
            bids=bids,
            asks=(make_level("101", "15"),),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )
        snapshot2 = OrderBookSnapshot(
            bids=bids,
            asks=(make_level("102", "15"),),
            timestamp=1000.0,
            symbol="BTCUSDT",
        )

        assert snapshot1 != snapshot2

    def test_different_timestamps_are_not_equal(self, make_level) -> None:
        bids = (make_level("100", "10"),)
        asks = (make_level("101", "15"),)

        snapshot1 = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )
        snapshot2 = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=2000.0,
            symbol="BTCUSDT",
        )

        assert snapshot1 != snapshot2

    def test_different_symbols_are_not_equal(self, make_level) -> None:
        bids = (make_level("100", "10"),)
        asks = (make_level("101", "15"),)

        snapshot1 = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=1000.0,
            symbol="BTCUSDT",
        )
        snapshot2 = OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=1000.0,
            symbol="ETHUSDT",
        )

        assert snapshot1 != snapshot2
