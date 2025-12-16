"""
Tests for ExponentialBackoff - TDD RED stage.

These tests define the expected behavior of the ExponentialBackoff class
used for reconnection delays in the Binance WebSocket connector.

Requirements covered:
    R1: Initial delay equals base_delay
    R2: Each subsequent call multiplies delay by multiplier
    R3: Delay never exceeds max_delay
    R4: reset() returns delay to base_delay
    R5: Default constructor values are sensible
"""

import pytest

# This import will fail until implementation exists (RED stage)
from connector_binance.backoff import ExponentialBackoff

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def default_backoff() -> ExponentialBackoff:
    """Backoff with explicit configuration: base=1s, multiplier=2, max=60s."""
    return ExponentialBackoff(
        base_delay=1.0,
        multiplier=2.0,
        max_delay=60.0,
    )


@pytest.fixture
def small_max_backoff() -> ExponentialBackoff:
    """Backoff with small max to test capping quickly."""
    return ExponentialBackoff(
        base_delay=1.0,
        multiplier=2.0,
        max_delay=5.0,
    )


# =============================================================================
# Category 1: Initial Delay (R1)
# =============================================================================


class TestInitialDelay:
    """Tests for initial delay behavior."""

    def test_initial_delay_equals_base_delay(self, default_backoff: ExponentialBackoff) -> None:
        """R1: First call to next_delay() returns base_delay."""
        delay = default_backoff.next_delay()

        assert delay == 1.0

    def test_initial_delay_with_custom_base(self) -> None:
        """R1: Initial delay respects custom base_delay."""
        backoff = ExponentialBackoff(base_delay=5.0, multiplier=2.0, max_delay=100.0)

        delay = backoff.next_delay()

        assert delay == 5.0

    def test_initial_delay_with_fractional_base(self) -> None:
        """R1: Fractional base_delay is supported."""
        backoff = ExponentialBackoff(base_delay=0.5, multiplier=2.0, max_delay=60.0)

        delay = backoff.next_delay()

        assert delay == 0.5


# =============================================================================
# Category 2: Exponential Growth (R2)
# =============================================================================


class TestExponentialGrowth:
    """Tests for exponential delay growth."""

    def test_delay_multiplies_on_subsequent_calls(
        self, default_backoff: ExponentialBackoff
    ) -> None:
        """R2: Each call to next_delay() multiplies by multiplier."""
        first = default_backoff.next_delay()
        second = default_backoff.next_delay()
        third = default_backoff.next_delay()

        assert first == 1.0
        assert second == 2.0
        assert third == 4.0

    def test_growth_sequence_with_custom_multiplier(self) -> None:
        """R2: Custom multiplier (3x) produces correct sequence."""
        backoff = ExponentialBackoff(base_delay=1.0, multiplier=3.0, max_delay=1000.0)

        delays = [backoff.next_delay() for _ in range(4)]

        assert delays == [1.0, 3.0, 9.0, 27.0]

    def test_growth_with_fractional_multiplier(self) -> None:
        """R2: Fractional multiplier (1.5x) produces correct sequence."""
        backoff = ExponentialBackoff(base_delay=2.0, multiplier=1.5, max_delay=100.0)

        first = backoff.next_delay()
        second = backoff.next_delay()
        third = backoff.next_delay()

        assert first == 2.0
        assert second == 3.0
        assert third == 4.5


# =============================================================================
# Category 3: Maximum Delay Cap (R3)
# =============================================================================


class TestMaxDelayCap:
    """Tests for max_delay capping behavior."""

    def test_delay_caps_at_max_delay(self, small_max_backoff: ExponentialBackoff) -> None:
        """R3: Delay never exceeds max_delay."""
        # Sequence: 1, 2, 4, 8 -> capped at 5
        delays = [small_max_backoff.next_delay() for _ in range(5)]

        assert delays == [1.0, 2.0, 4.0, 5.0, 5.0]

    def test_cap_applies_immediately_when_base_exceeds_max(self) -> None:
        """R3: If base_delay > max_delay, cap applies from first call."""
        backoff = ExponentialBackoff(base_delay=10.0, multiplier=2.0, max_delay=5.0)

        delay = backoff.next_delay()

        assert delay == 5.0

    def test_subsequent_calls_remain_capped(self, small_max_backoff: ExponentialBackoff) -> None:
        """R3: After hitting cap, all subsequent calls return max_delay."""
        # Get past the cap
        for _ in range(10):
            small_max_backoff.next_delay()

        # Should still return max_delay
        delay = small_max_backoff.next_delay()

        assert delay == 5.0


# =============================================================================
# Category 4: Reset Behavior (R4)
# =============================================================================


class TestReset:
    """Tests for reset() functionality."""

    def test_reset_returns_to_base_delay(self, default_backoff: ExponentialBackoff) -> None:
        """R4: After reset(), next_delay() returns base_delay again."""
        # Advance the backoff
        default_backoff.next_delay()  # 1
        default_backoff.next_delay()  # 2
        default_backoff.next_delay()  # 4

        default_backoff.reset()
        delay = default_backoff.next_delay()

        assert delay == 1.0

    def test_reset_after_hitting_cap(self, small_max_backoff: ExponentialBackoff) -> None:
        """R4: Reset works even after delay was capped."""
        # Hit the cap
        for _ in range(10):
            small_max_backoff.next_delay()

        small_max_backoff.reset()
        delay = small_max_backoff.next_delay()

        assert delay == 1.0

    def test_multiple_resets_are_idempotent(self, default_backoff: ExponentialBackoff) -> None:
        """R4: Multiple consecutive resets are safe."""
        default_backoff.next_delay()
        default_backoff.next_delay()

        default_backoff.reset()
        default_backoff.reset()
        default_backoff.reset()

        delay = default_backoff.next_delay()

        assert delay == 1.0

    def test_reset_on_fresh_instance_is_safe(self, default_backoff: ExponentialBackoff) -> None:
        """R4: Calling reset() on fresh instance does not break it."""
        default_backoff.reset()
        delay = default_backoff.next_delay()

        assert delay == 1.0


# =============================================================================
# Category 5: Default Values (R5)
# =============================================================================


class TestDefaultValues:
    """Tests for default constructor values."""

    def test_default_values(self) -> None:
        """R5: Default constructor uses sensible defaults."""
        backoff = ExponentialBackoff()

        # First delay should be the default base_delay
        first_delay = backoff.next_delay()

        # Should be reasonable defaults (e.g., 1s base, 2x multiplier, 60s max)
        assert first_delay > 0
        assert first_delay <= 5.0  # base_delay should be <= 5 seconds

    def test_default_max_is_reasonable(self) -> None:
        """R5: Default max_delay prevents runaway delays."""
        backoff = ExponentialBackoff()

        # Call many times to ensure cap is applied
        for _ in range(20):
            delay = backoff.next_delay()

        # Max should be capped at a reasonable value (e.g., <= 120 seconds)
        assert delay <= 120.0

    def test_default_growth_is_exponential(self) -> None:
        """R5: Default multiplier produces exponential growth."""
        backoff = ExponentialBackoff()

        first = backoff.next_delay()
        second = backoff.next_delay()

        # Second delay should be greater than first (exponential growth)
        assert second > first


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for boundary conditions and special scenarios."""

    def test_zero_base_delay(self) -> None:
        """Edge: Zero base_delay should work (immediate retry)."""
        backoff = ExponentialBackoff(base_delay=0.0, multiplier=2.0, max_delay=10.0)

        delay = backoff.next_delay()

        assert delay == 0.0

    def test_multiplier_of_one_keeps_constant_delay(self) -> None:
        """Edge: Multiplier of 1.0 keeps delay constant."""
        backoff = ExponentialBackoff(base_delay=5.0, multiplier=1.0, max_delay=60.0)

        delays = [backoff.next_delay() for _ in range(5)]

        assert all(d == 5.0 for d in delays)

    def test_very_large_number_of_calls(self) -> None:
        """Edge: Many calls do not cause overflow or errors."""
        backoff = ExponentialBackoff(base_delay=1.0, multiplier=2.0, max_delay=60.0)

        # Call 100 times - should never error and always return <= max_delay
        delays = [backoff.next_delay() for _ in range(100)]

        assert all(d <= 60.0 for d in delays)
        assert all(d > 0 for d in delays)
