"""Unit tests for the Watcher class.

These tests verify the core processing pipeline:
- Extract top N levels from order book snapshots
- Sum volumes for bids and asks
- Compute imbalance ratio
- Evaluate signal against threshold with cooldown
- Send alert if triggered

Tests use FakeClock for deterministic time and FakeAlertNotifier
to inspect sent alerts.
"""

import pytest
from domain_imbalance import imbalance_ratio
from signal_engine import EngineConfig, SignalEvaluator
from testkit import FakeClock, orderbook_builder

from orderbook_watcher.testing import FakeAlertNotifier
from orderbook_watcher.watcher import Watcher


@pytest.fixture
def signal_evaluator(fake_clock: FakeClock) -> SignalEvaluator:
    """Create a SignalEvaluator with default test configuration and fake clock."""
    config = EngineConfig(
        threshold=0.35,
        cooldown_seconds=30.0,
        hysteresis_enabled=False,
    )
    return SignalEvaluator(config, fake_clock)


@pytest.fixture
def watcher(
    signal_evaluator: SignalEvaluator,
    fake_notifier: FakeAlertNotifier,
) -> Watcher:
    """Create a Watcher with injected test dependencies."""
    return Watcher(
        evaluator=signal_evaluator,
        notifier=fake_notifier,
        threshold=0.35,
        top_n_levels=10,
    )


class TestWatcherProcessSnapshot:
    """Tests for Watcher.process_snapshot method."""

    @pytest.mark.asyncio
    async def test_process_snapshot_below_threshold_no_alert(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """When imbalance ratio is below threshold, no alert is sent."""
        # Arrange: Build a snapshot with balanced bids/asks (ratio = 0.0)
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "1.0"), ("44999.00", "1.0")])
            .with_asks([("45001.00", "1.0"), ("45002.00", "1.0")])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert
        assert fake_notifier.call_count == 0

    @pytest.mark.asyncio
    async def test_process_snapshot_above_threshold_sends_alert(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """When imbalance ratio exceeds threshold, an alert is sent with correct payload."""
        # Arrange: Build a snapshot with high bid volume (ratio > 0.35)
        # bid_volume = 8.0, ask_volume = 2.0 => ratio = (8-2)/(8+2) = 0.6
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "4.0"), ("44999.00", "4.0")])
            .with_asks([("45001.00", "1.0"), ("45002.00", "1.0")])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert
        assert fake_notifier.call_count == 1
        alert = fake_notifier.last_call
        assert alert is not None
        assert alert.symbol == "BTCUSDT"
        assert alert.ratio == pytest.approx(0.6)
        assert alert.bid_volume == pytest.approx(8.0)
        assert alert.ask_volume == pytest.approx(2.0)
        assert alert.threshold == 0.35

    @pytest.mark.asyncio
    async def test_process_snapshot_cooldown_prevents_duplicate_alerts(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """Two above-threshold snapshots within cooldown period only trigger one alert."""
        # Arrange: High imbalance snapshot
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        # Act: Process first snapshot
        await watcher.process_snapshot(snapshot)

        # Advance time by less than cooldown (30 seconds)
        fake_clock.advance(seconds=15)

        # Process second snapshot (still above threshold)
        await watcher.process_snapshot(snapshot)

        # Assert: Only one alert was sent
        assert fake_notifier.call_count == 1

    @pytest.mark.asyncio
    async def test_process_snapshot_after_cooldown_sends_alert(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """Second snapshot after cooldown expires triggers another alert."""
        # Arrange: High imbalance snapshot
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        # Act: Process first snapshot
        await watcher.process_snapshot(snapshot)

        # Advance time beyond cooldown (30+ seconds)
        fake_clock.advance(seconds=31)

        # Process second snapshot
        await watcher.process_snapshot(snapshot)

        # Assert: Two alerts were sent
        assert fake_notifier.call_count == 2

    @pytest.mark.asyncio
    async def test_process_snapshot_correct_ratio_calculation(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Verify the ratio calculation matches expected formula."""
        # Arrange: Specific volumes for precise ratio calculation
        # bid_volume = 7.5, ask_volume = 2.5 => ratio = (7.5-2.5)/(7.5+2.5) = 0.5
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0"), ("44999.00", "2.5")])
            .with_asks([("45001.00", "1.5"), ("45002.00", "1.0")])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert
        alert = fake_notifier.last_call
        assert alert is not None

        # Calculate expected ratio using the same formula
        expected_ratio = imbalance_ratio(7.5, 2.5)
        assert alert.ratio == pytest.approx(expected_ratio)
        assert alert.ratio == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_process_snapshot_uses_top_n_levels(
        self,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """Watcher only uses top N levels for calculation."""
        # Create watcher with top_n_levels=2
        config = EngineConfig(threshold=0.35, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)
        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=2,
        )

        # Arrange: Snapshot with many levels but top 2 have specific volumes
        # Top 2 bids (by price desc): 45000.00 @ 3.0, 44999.00 @ 2.0 => bid_vol = 5.0
        # Top 2 asks (by price asc): 45001.00 @ 1.0, 45002.00 @ 0.5 => ask_vol = 1.5
        # ratio = (5.0 - 1.5) / (5.0 + 1.5) = 3.5 / 6.5 ~= 0.538
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids(
                [
                    ("45000.00", "3.0"),
                    ("44999.00", "2.0"),
                    ("44998.00", "100.0"),  # Should be ignored (not in top 2)
                ]
            )
            .with_asks(
                [
                    ("45001.00", "1.0"),
                    ("45002.00", "0.5"),
                    ("45003.00", "100.0"),  # Should be ignored (not in top 2)
                ]
            )
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert: Alert sent with volumes from only top 2 levels
        assert fake_notifier.call_count == 1
        alert = fake_notifier.last_call
        assert alert is not None
        assert alert.bid_volume == pytest.approx(5.0)
        assert alert.ask_volume == pytest.approx(1.5)
        assert alert.ratio == pytest.approx(3.5 / 6.5)

    @pytest.mark.asyncio
    async def test_process_snapshot_empty_orderbook_no_alert(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Empty orderbook (no bids or asks) produces ratio 0.0, no alert."""
        # Arrange: Empty bids and asks
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([])
            .with_asks([])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert: No alert (ratio = 0.0 which is below threshold)
        assert fake_notifier.call_count == 0

    @pytest.mark.asyncio
    async def test_process_snapshot_notifier_transient_error_continues(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """Transient notifier error is logged but processing continues."""
        # Arrange
        fake_notifier.set_transient_error("Network timeout")

        # High imbalance snapshot
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        # Act: Should not raise, should continue processing
        await watcher.process_snapshot(snapshot)

        # Clear error for next call
        fake_notifier.clear_error()
        fake_clock.advance(seconds=31)

        # Process another snapshot - should still work
        await watcher.process_snapshot(snapshot)

        # Assert: Both attempts made (notifier was called both times)
        assert fake_notifier.call_count == 2

    @pytest.mark.asyncio
    async def test_process_snapshot_notifier_permanent_error_continues(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """Permanent notifier error is logged but processing continues."""
        # Arrange
        fake_notifier.set_permanent_error("Invalid token")

        # High imbalance snapshot
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        # Act: Should not raise, should continue processing
        await watcher.process_snapshot(snapshot)

        # Clear error for next call
        fake_notifier.clear_error()
        fake_clock.advance(seconds=31)

        # Process another snapshot - should still work
        await watcher.process_snapshot(snapshot)

        # Assert: Both attempts made
        assert fake_notifier.call_count == 2


class TestWatcherEdgeCases:
    """Edge case tests for Watcher."""

    @pytest.mark.asyncio
    async def test_exactly_at_threshold_no_alert(
        self,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """When ratio exactly equals threshold, no alert (threshold check is >)."""
        config = EngineConfig(threshold=0.5, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)
        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.5,
            top_n_levels=10,
        )

        # Arrange: ratio = (3-1)/(3+1) = 0.5 exactly
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "3.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert: No alert because ratio is not > threshold
        assert fake_notifier.call_count == 0

    @pytest.mark.asyncio
    async def test_multiple_symbols_independent_cooldown(
        self,
        fake_notifier: FakeAlertNotifier,
        fake_clock: FakeClock,
    ) -> None:
        """Different symbols have independent cooldown tracking."""
        config = EngineConfig(threshold=0.35, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)
        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=10,
        )

        # High imbalance snapshots for two different symbols
        btc_snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        eth_snapshot = (
            orderbook_builder()
            .with_symbol("ETHUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("3000.00", "5.0")])
            .with_asks([("3001.00", "1.0")])
            .build()
        )

        # Act: Process BTC
        await watcher.process_snapshot(btc_snapshot)

        # Process ETH right after (should alert, different symbol)
        await watcher.process_snapshot(eth_snapshot)

        # Assert: Both symbols alerted
        assert fake_notifier.call_count == 2
        assert fake_notifier.was_called_for_symbol("BTCUSDT")
        assert fake_notifier.was_called_for_symbol("ETHUSDT")

    @pytest.mark.asyncio
    async def test_alert_payload_timestamp_from_snapshot(
        self,
        watcher: Watcher,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Alert payload contains the snapshot timestamp."""
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320123.456)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        await watcher.process_snapshot(snapshot)

        alert = fake_notifier.last_call
        assert alert is not None
        assert alert.timestamp == 1705320123.456
