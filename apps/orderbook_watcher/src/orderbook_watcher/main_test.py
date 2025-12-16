"""Integration tests for the orderbook_watcher main module.

These tests verify the end-to-end wiring of the application:
- Configuration loading
- Component creation and dependency injection
- Snapshot processing through the full pipeline
- Graceful shutdown behavior
"""

from datetime import datetime, timezone

import pytest
from signal_engine import EngineConfig, SignalEvaluator
from testkit import FakeClock, orderbook_builder

from orderbook_watcher.testing import FakeAlertNotifier
from orderbook_watcher.watcher import Watcher


class TestAsyncMainProcessesSnapshot:
    """Integration tests for main processing flow."""

    @pytest.mark.asyncio
    async def test_async_main_processes_snapshot_and_sends_alert(
        self,
        fake_clock: FakeClock,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """End-to-end test: snapshot processing triggers alert when threshold exceeded."""
        # Arrange: Create components with test configuration
        config = EngineConfig(
            threshold=0.35,
            cooldown_seconds=30.0,
            hysteresis_enabled=False,
        )
        evaluator = SignalEvaluator(config, fake_clock)

        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=10,
        )

        # Create a high-imbalance snapshot (ratio = 0.6)
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "4.0"), ("44999.00", "4.0")])
            .with_asks([("45001.00", "1.0"), ("45002.00", "1.0")])
            .build()
        )

        # Act: Process the snapshot
        await watcher.process_snapshot(snapshot)

        # Assert: Alert was sent with correct data
        assert fake_notifier.call_count == 1
        alert = fake_notifier.last_call
        assert alert is not None
        assert alert.symbol == "BTCUSDT"
        assert alert.ratio == pytest.approx(0.6)
        assert alert.bid_volume == pytest.approx(8.0)
        assert alert.ask_volume == pytest.approx(2.0)
        assert alert.threshold == 0.35
        assert alert.timestamp == 1705320000.0


class TestMainWiring:
    """Tests for main module component wiring."""

    @pytest.mark.asyncio
    async def test_evaluator_uses_injected_clock(
        self,
        fake_clock: FakeClock,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Evaluator uses the injected clock for time-based cooldown decisions."""
        # Arrange
        config = EngineConfig(threshold=0.35, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)

        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=10,
        )

        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "5.0")])
            .with_asks([("45001.00", "1.0")])
            .build()
        )

        # Act: Process first alert
        await watcher.process_snapshot(snapshot)
        assert fake_notifier.call_count == 1

        # Advance fake clock beyond cooldown
        fake_clock.advance(seconds=35)

        # Act: Process second alert (should trigger because cooldown expired)
        await watcher.process_snapshot(snapshot)

        # Assert: Second alert was sent
        assert fake_notifier.call_count == 2

    @pytest.mark.asyncio
    async def test_watcher_uses_injected_notifier(
        self,
        fake_clock: FakeClock,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Watcher uses the injected notifier to send alerts."""
        # Arrange
        config = EngineConfig(threshold=0.35, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)

        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=10,
        )

        snapshot = (
            orderbook_builder()
            .with_symbol("ETHUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("3000.00", "5.0")])
            .with_asks([("3001.00", "1.0")])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert: Notifier received the alert
        assert fake_notifier.was_called_for_symbol("ETHUSDT")

    @pytest.mark.asyncio
    async def test_watcher_uses_injected_evaluator(
        self,
        fake_clock: FakeClock,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Watcher uses the injected evaluator for threshold decisions."""
        # Arrange with different threshold
        # High threshold that won't be exceeded
        config = EngineConfig(threshold=0.9, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)

        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.9,  # Same high threshold
            top_n_levels=10,
        )

        # ratio = 0.6 which is below 0.9
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

        # Assert: No alert because ratio (0.6) is below threshold (0.9)
        assert fake_notifier.call_count == 0


class TestMainConfiguration:
    """Tests for configuration handling in main."""

    @pytest.mark.asyncio
    async def test_top_n_levels_configuration_affects_calculation(
        self,
        fake_clock: FakeClock,
        fake_notifier: FakeAlertNotifier,
    ) -> None:
        """Different top_n_levels values affect volume calculations."""
        config = EngineConfig(threshold=0.35, cooldown_seconds=30.0)
        evaluator = SignalEvaluator(config, fake_clock)

        # Watcher with top_n_levels=1
        watcher = Watcher(
            evaluator=evaluator,
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=1,  # Only top 1 level
        )

        # Snapshot where top 1 level has different imbalance than all levels
        # Top 1 bid: 45000.00 @ 2.0, Top 1 ask: 45001.00 @ 1.0
        # ratio with top 1 = (2-1)/(2+1) = 0.333... (below 0.35)
        snapshot = (
            orderbook_builder()
            .with_symbol("BTCUSDT")
            .with_timestamp(1705320000.0)
            .with_bids([("45000.00", "2.0"), ("44999.00", "10.0")])
            .with_asks([("45001.00", "1.0"), ("45002.00", "0.1")])
            .build()
        )

        # Act
        await watcher.process_snapshot(snapshot)

        # Assert: No alert with top_n=1 (ratio 0.333)
        assert fake_notifier.call_count == 0

        # Now test with top_n_levels=2 (need fresh clock and evaluator for independent test)
        fake_clock2 = FakeClock(datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))
        fake_notifier.reset()
        watcher2 = Watcher(
            evaluator=SignalEvaluator(config, fake_clock2),
            notifier=fake_notifier,
            threshold=0.35,
            top_n_levels=2,  # Top 2 levels
        )

        # ratio with top 2 = (2+10-1-0.1)/(2+10+1+0.1) = 10.9/13.1 ~= 0.832
        await watcher2.process_snapshot(snapshot)

        # Assert: Alert sent with top_n=2 (ratio 0.832)
        assert fake_notifier.call_count == 1
