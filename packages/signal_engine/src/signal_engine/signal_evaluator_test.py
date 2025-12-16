"""
Tests for SignalEvaluator.

These tests verify the behavior of the signal_engine package.

Requirements covered:
    R1: Threshold check - Alert when ratio > threshold
    R2: Cooldown enforcement - Suppress alerts during cooldown period
    R3: Hysteresis - Optional re-arm logic requiring ratio to drop below threshold - delta
    R4: Independent symbol state - Each symbol tracks its own state
    R5: First evaluation - No cooldown on first evaluation for a symbol
    R6: Negative ratios - Never trigger alerts
    R7: Edge cases - ratio = threshold exactly should NOT alert
"""

from datetime import datetime

import pytest
from testkit import FakeClock

from signal_engine import EngineConfig, SignalEvaluator

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def fake_clock() -> FakeClock:
    """Deterministic clock for tests starting at a fixed base time."""
    return FakeClock(datetime(2025, 1, 1, 12, 0, 0))


@pytest.fixture
def default_config() -> EngineConfig:
    """Standard configuration: threshold=0.35, cooldown=30s, no hysteresis."""
    return EngineConfig(
        threshold=0.35,
        cooldown_seconds=30.0,
        hysteresis_enabled=False,
        hysteresis_delta=0.0,
    )


@pytest.fixture
def hysteresis_config() -> EngineConfig:
    """Configuration with hysteresis enabled: threshold=0.35, delta=0.10."""
    return EngineConfig(
        threshold=0.35,
        cooldown_seconds=30.0,
        hysteresis_enabled=True,
        hysteresis_delta=0.10,
    )


@pytest.fixture
def evaluator(default_config: EngineConfig, fake_clock: FakeClock) -> SignalEvaluator:
    """SignalEvaluator with default configuration and fake clock."""
    return SignalEvaluator(default_config, fake_clock)


@pytest.fixture
def hysteresis_evaluator(
    hysteresis_config: EngineConfig, fake_clock: FakeClock
) -> SignalEvaluator:
    """SignalEvaluator with hysteresis enabled and fake clock."""
    return SignalEvaluator(hysteresis_config, fake_clock)


@pytest.fixture
def zero_cooldown_config() -> EngineConfig:
    """Configuration with zero cooldown for consecutive alert tests."""
    return EngineConfig(
        threshold=0.35,
        cooldown_seconds=0.0,
        hysteresis_enabled=False,
        hysteresis_delta=0.0,
    )


@pytest.fixture
def zero_cooldown_evaluator(
    zero_cooldown_config: EngineConfig, fake_clock: FakeClock
) -> SignalEvaluator:
    """SignalEvaluator with zero cooldown and fake clock."""
    return SignalEvaluator(zero_cooldown_config, fake_clock)


@pytest.fixture
def high_threshold_config() -> EngineConfig:
    """Configuration with high threshold (0.95) for extreme imbalance tests."""
    return EngineConfig(
        threshold=0.95,
        cooldown_seconds=30.0,
        hysteresis_enabled=False,
        hysteresis_delta=0.0,
    )


@pytest.fixture
def high_threshold_evaluator(
    high_threshold_config: EngineConfig, fake_clock: FakeClock
) -> SignalEvaluator:
    """SignalEvaluator with high threshold and fake clock."""
    return SignalEvaluator(high_threshold_config, fake_clock)


# =============================================================================
# Category 1: Threshold Logic (R1, R7)
# =============================================================================


class TestThresholdLogic:
    """Tests for basic threshold comparison logic."""

    def test_ratio_above_threshold_triggers_alert(
        self, evaluator: SignalEvaluator
    ) -> None:
        """R1: When ratio > threshold, should_alert is True."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=0.40)

        assert decision.should_alert is True
        assert decision.symbol == "BTCUSDT"
        assert decision.ratio == 0.40

    def test_ratio_below_threshold_does_not_alert(
        self, evaluator: SignalEvaluator
    ) -> None:
        """R1: When ratio < threshold, should_alert is False."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=0.20)

        assert decision.should_alert is False
        assert decision.symbol == "BTCUSDT"
        assert decision.ratio == 0.20

    def test_ratio_equal_to_threshold_does_not_alert(
        self, evaluator: SignalEvaluator
    ) -> None:
        """R7: When ratio == threshold exactly, should_alert is False (strict >)."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=0.35)

        assert decision.should_alert is False

    def test_ratio_just_above_threshold_triggers_alert(
        self, evaluator: SignalEvaluator
    ) -> None:
        """R1: Ratio barely above threshold (0.35 + epsilon) should trigger."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=0.350001)

        assert decision.should_alert is True

    @pytest.mark.parametrize(
        "ratio,expected_alert",
        [
            (0.34, False),
            (0.349999, False),
            (0.35, False),
            (0.350001, True),
            (0.36, True),
            (0.50, True),
            (0.99, True),
            (1.0, True),
        ],
    )
    def test_threshold_boundary_parametrized(
        self,
        evaluator: SignalEvaluator,
        ratio: float,
        expected_alert: bool,
    ) -> None:
        """R1/R7: Parametrized boundary tests around threshold=0.35."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=ratio)

        assert decision.should_alert is expected_alert


# =============================================================================
# Category 2: Negative Ratios (R6)
# =============================================================================


class TestNegativeRatios:
    """Tests ensuring negative ratios never trigger alerts."""

    @pytest.mark.parametrize(
        "ratio",
        [-1.0, -0.99, -0.5, -0.35, -0.1, -0.001, 0.0],
    )
    def test_non_positive_ratios_never_alert(
        self, evaluator: SignalEvaluator, ratio: float
    ) -> None:
        """R6: All non-positive ratios should never alert."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=ratio)

        assert decision.should_alert is False


# =============================================================================
# Category 3: Cooldown (R2)
# =============================================================================


class TestCooldown:
    """Tests for cooldown enforcement after alerts."""

    def test_second_alert_within_cooldown_is_suppressed(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R2: After alerting, second evaluation within cooldown should not alert."""
        # First alert triggers
        first = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert first.should_alert is True

        # Second evaluation within 30s cooldown
        fake_clock.advance(seconds=15)
        second = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert second.should_alert is False
        assert "cooldown" in second.reason.lower()

    def test_alert_after_cooldown_expires_triggers(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R2: After cooldown expires, new alert should trigger."""
        # First alert
        first = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert first.should_alert is True

        # After cooldown (30s + 1s)
        fake_clock.advance(seconds=31)
        second = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert second.should_alert is True

    def test_alert_exactly_at_cooldown_boundary_triggers(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R2: At exactly cooldown_seconds, alert should trigger (cooldown expired)."""
        # First alert
        first = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert first.should_alert is True

        # Exactly at cooldown boundary (30s)
        fake_clock.advance(seconds=30)
        second = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert second.should_alert is True

    def test_cooldown_resets_after_new_alert(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R2: After a new alert, cooldown resets for another 30s."""
        # First alert at t=0
        evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # Second alert at t=31s (after first cooldown)
        fake_clock.advance(seconds=31)
        second = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert second.should_alert is True

        # Third attempt at t=46s (15s after second alert, within new cooldown)
        fake_clock.advance(seconds=15)
        third = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert third.should_alert is False


# =============================================================================
# Category 4: First Evaluation (R5)
# =============================================================================


class TestFirstEvaluation:
    """Tests for first-time symbol evaluation behavior."""

    def test_first_evaluation_for_symbol_has_no_cooldown(
        self, evaluator: SignalEvaluator
    ) -> None:
        """R5: First evaluation for a new symbol should not have any cooldown."""
        decision = evaluator.evaluate(symbol="DOTUSDT", ratio=0.50)

        assert decision.should_alert is True

    def test_first_evaluation_below_threshold_does_not_alert(
        self, evaluator: SignalEvaluator
    ) -> None:
        """R5: First evaluation below threshold should not alert (threshold still applies)."""
        decision = evaluator.evaluate(symbol="DOTUSDT", ratio=0.20)

        assert decision.should_alert is False


# =============================================================================
# Category 5: Independent Symbol State (R4)
# =============================================================================


class TestIndependentSymbolState:
    """Tests ensuring each symbol has independent state."""

    def test_different_symbols_have_independent_cooldowns(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R4: Alert for BTCUSDT should not affect cooldown of DOTUSDT."""
        # Alert for BTCUSDT
        btc_alert = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert btc_alert.should_alert is True

        # Immediately evaluate DOTUSDT - should alert (no cooldown for DOT)
        dot_alert = evaluator.evaluate(symbol="DOTUSDT", ratio=0.50)
        assert dot_alert.should_alert is True

        # BTC within cooldown should not alert
        fake_clock.advance(seconds=10)
        btc_within_cooldown = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert btc_within_cooldown.should_alert is False

    def test_multiple_symbols_track_state_independently(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R4: Multiple symbols should each track their own cooldown timers."""
        # Alert for all symbols at different times
        # t=0: BTC alerts
        evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # t=5: DOT alerts
        fake_clock.advance(seconds=5)
        evaluator.evaluate(symbol="DOTUSDT", ratio=0.50)

        # t=10: SOL alerts
        fake_clock.advance(seconds=5)
        evaluator.evaluate(symbol="SOLUSDT", ratio=0.50)

        # At t=31: BTC cooldown expired (31s), DOT still in cooldown (26s), SOL in cooldown (21s)
        fake_clock.advance(seconds=21)
        btc_at_31 = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        dot_at_31 = evaluator.evaluate(symbol="DOTUSDT", ratio=0.50)
        sol_at_31 = evaluator.evaluate(symbol="SOLUSDT", ratio=0.50)

        assert btc_at_31.should_alert is True  # 31s elapsed since t=0
        assert (
            dot_at_31.should_alert is False
        )  # 26s elapsed since t=5, still in cooldown
        assert (
            sol_at_31.should_alert is False
        )  # 21s elapsed since t=10, still in cooldown


# =============================================================================
# Category 6: Hysteresis (R3)
# =============================================================================


class TestHysteresis:
    """Tests for hysteresis logic (optional re-arm requirement)."""

    def test_hysteresis_blocks_alert_until_ratio_drops_below_rearm_level(
        self, hysteresis_evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R3: After alert, must drop below threshold - delta before re-arming."""
        # threshold=0.35, delta=0.10, so re-arm level = 0.25

        # First alert
        first = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert first.should_alert is True

        # After cooldown, but ratio still above re-arm level (0.30 > 0.25)
        fake_clock.advance(seconds=35)
        still_high = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.30)

        # Should not alert because ratio hasn't dropped below re-arm level
        assert still_high.should_alert is False

    def test_hysteresis_allows_alert_after_ratio_drops_and_rises(
        self, hysteresis_evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R3: After dropping below re-arm level and rising again, should alert."""
        # First alert at t=0
        hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # At t=35s, ratio drops to 0.20 (below re-arm level 0.25) - re-arms
        fake_clock.advance(seconds=35)
        low = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.20)
        assert low.should_alert is False  # Below threshold, no alert

        # At t=36s, ratio rises above threshold again - should alert
        fake_clock.advance(seconds=1)
        high_again = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert high_again.should_alert is True

    def test_hysteresis_exact_rearm_boundary(
        self, hysteresis_evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R3: At exactly threshold - delta, should re-arm (boundary test)."""
        # threshold=0.35, delta=0.10, re-arm level = 0.25

        # First alert
        hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # After cooldown, ratio at exactly re-arm level (0.25)
        fake_clock.advance(seconds=35)
        at_rearm = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.25)
        assert at_rearm.should_alert is False  # Below threshold

        # Rise above threshold - should alert (re-armed at 0.25)
        fake_clock.advance(seconds=1)
        high = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert high.should_alert is True

    def test_hysteresis_just_above_rearm_level_does_not_rearm(
        self, hysteresis_evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R3: Ratio just above re-arm level should NOT re-arm."""
        # threshold=0.35, delta=0.10, re-arm level = 0.25

        # First alert
        hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # After cooldown, ratio at 0.251 (just above 0.25) - should not re-arm
        fake_clock.advance(seconds=35)
        hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.251)

        # Try to trigger alert - should fail (not re-armed)
        fake_clock.advance(seconds=1)
        attempt = hysteresis_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert attempt.should_alert is False

    def test_hysteresis_disabled_allows_immediate_realert_after_cooldown(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """R3: With hysteresis disabled, can alert immediately after cooldown."""
        # First alert
        evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # After cooldown, ratio still high - should alert (no hysteresis)
        fake_clock.advance(seconds=35)
        second = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert second.should_alert is True


# =============================================================================
# Category 7: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for boundary conditions and special scenarios."""

    def test_extreme_positive_ratio(self, evaluator: SignalEvaluator) -> None:
        """Edge: Extreme positive ratio (1.0 = all bids) should alert."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=1.0)
        assert decision.should_alert is True

    def test_extreme_negative_ratio(self, evaluator: SignalEvaluator) -> None:
        """Edge: Extreme negative ratio (-1.0 = all asks) should not alert."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=-1.0)
        assert decision.should_alert is False

    def test_very_small_positive_ratio(self, evaluator: SignalEvaluator) -> None:
        """Edge: Very small positive ratio (0.001) should not alert (below threshold)."""
        decision = evaluator.evaluate(symbol="BTCUSDT", ratio=0.001)
        assert decision.should_alert is False

    def test_zero_cooldown_allows_consecutive_alerts(
        self, zero_cooldown_evaluator: SignalEvaluator
    ) -> None:
        """Edge: With cooldown=0, consecutive alerts should all trigger."""
        first = zero_cooldown_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        second = zero_cooldown_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        third = zero_cooldown_evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        assert first.should_alert is True
        assert second.should_alert is True
        assert third.should_alert is True

    def test_very_high_threshold_rarely_alerts(
        self, high_threshold_evaluator: SignalEvaluator
    ) -> None:
        """Edge: High threshold (0.95) means only extreme imbalances alert."""
        moderate = high_threshold_evaluator.evaluate(symbol="BTCUSDT", ratio=0.80)
        assert moderate.should_alert is False

        extreme = high_threshold_evaluator.evaluate(symbol="BTCUSDT", ratio=0.96)
        assert extreme.should_alert is True

    def test_alert_decision_contains_correct_metadata(
        self, evaluator: SignalEvaluator
    ) -> None:
        """Edge: AlertDecision should contain correct symbol and ratio."""
        decision = evaluator.evaluate(symbol="SOLUSDT", ratio=0.42)

        assert decision.symbol == "SOLUSDT"
        assert decision.ratio == 0.42
        assert isinstance(decision.reason, str)
        assert len(decision.reason) > 0

    def test_rapid_alternating_symbols(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """Edge: Rapidly alternating between symbols should handle state correctly."""
        symbols = ["BTCUSDT", "DOTUSDT", "SOLUSDT"]

        # Alert for each symbol
        for i, symbol in enumerate(symbols):
            fake_clock.advance(microseconds=1000 * i)  # 1ms per symbol
            decision = evaluator.evaluate(symbol=symbol, ratio=0.50)
            assert (
                decision.should_alert is True
            ), f"First alert for {symbol} should trigger"

        # Immediately try again for each - all should be in cooldown
        fake_clock.advance(seconds=1)
        for i, symbol in enumerate(symbols):
            fake_clock.advance(microseconds=1000 * i)  # 1ms per symbol
            decision = evaluator.evaluate(symbol=symbol, ratio=0.50)
            assert decision.should_alert is False, f"{symbol} should be in cooldown"

    @pytest.mark.parametrize(
        "cooldown_seconds",
        [0.0, 0.001, 1.0, 30.0, 60.0, 3600.0],
    )
    def test_various_cooldown_durations(self, cooldown_seconds: float) -> None:
        """Edge: Different cooldown durations should work correctly."""
        clock = FakeClock(datetime(2025, 1, 1, 12, 0, 0))
        config = EngineConfig(
            threshold=0.35,
            cooldown_seconds=cooldown_seconds,
            hysteresis_enabled=False,
            hysteresis_delta=0.0,
        )
        evaluator = SignalEvaluator(config, clock)

        # First alert
        first = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert first.should_alert is True

        # After cooldown expires
        clock.advance(seconds=int(cooldown_seconds), microseconds=1000)
        second = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert second.should_alert is True


# =============================================================================
# Integration-like Scenarios
# =============================================================================


class TestRealisticScenarios:
    """Tests simulating realistic usage patterns."""

    def test_typical_usage_scenario(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """Scenario: Typical series of evaluations for a single symbol."""
        symbol = "BTCUSDT"

        # t=0: Low imbalance - no alert
        d0 = evaluator.evaluate(symbol=symbol, ratio=0.15)
        assert d0.should_alert is False

        # t=5s: Imbalance rises above threshold - alert
        fake_clock.advance(seconds=5)
        d5 = evaluator.evaluate(symbol=symbol, ratio=0.45)
        assert d5.should_alert is True

        # t=10s: Still high but in cooldown - no alert
        fake_clock.advance(seconds=5)
        d10 = evaluator.evaluate(symbol=symbol, ratio=0.50)
        assert d10.should_alert is False

        # t=20s: Drops below threshold - no alert (expected)
        fake_clock.advance(seconds=10)
        d20 = evaluator.evaluate(symbol=symbol, ratio=0.20)
        assert d20.should_alert is False

        # t=40s: Rises again after cooldown - alert
        fake_clock.advance(seconds=20)
        d40 = evaluator.evaluate(symbol=symbol, ratio=0.50)
        assert d40.should_alert is True

    def test_multi_symbol_realistic_scenario(
        self, evaluator: SignalEvaluator, fake_clock: FakeClock
    ) -> None:
        """Scenario: Multiple symbols with different timing patterns."""
        # BTCUSDT alerts at t=0
        evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)

        # DOTUSDT starts below threshold at t=0
        d_dot_0 = evaluator.evaluate(symbol="DOTUSDT", ratio=0.20)
        assert d_dot_0.should_alert is False

        # DOTUSDT rises above threshold at t=10
        fake_clock.advance(seconds=10)
        d_dot_10 = evaluator.evaluate(symbol="DOTUSDT", ratio=0.40)
        assert d_dot_10.should_alert is True

        # BTCUSDT still in cooldown at t=20
        fake_clock.advance(seconds=10)
        d_btc_20 = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert d_btc_20.should_alert is False

        # BTCUSDT cooldown expired at t=31
        fake_clock.advance(seconds=11)
        d_btc_31 = evaluator.evaluate(symbol="BTCUSDT", ratio=0.50)
        assert d_btc_31.should_alert is True

        # DOTUSDT still in cooldown at t=35 (25s since t=10)
        fake_clock.advance(seconds=4)
        d_dot_35 = evaluator.evaluate(symbol="DOTUSDT", ratio=0.50)
        assert d_dot_35.should_alert is False

        # DOTUSDT cooldown expired at t=41 (31s since t=10)
        fake_clock.advance(seconds=6)
        d_dot_41 = evaluator.evaluate(symbol="DOTUSDT", ratio=0.50)
        assert d_dot_41.should_alert is True
