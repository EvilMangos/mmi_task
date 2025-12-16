"""Tests for the imbalance_ratio function.

These tests verify the core imbalance ratio calculation:
    Imbalance Ratio = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)

Requirements covered:
- R1: Core formula implementation
- R2: Division by zero handling (bid + ask == 0 returns 0.0)
- R3: Result range is [-1.0, 1.0] for valid inputs
- R4: All-bid (ask=0, bid>0) returns 1.0
- R5: All-ask (bid=0, ask>0) returns -1.0
- R6: Equal volumes return 0.0
"""

import pytest

from domain_imbalance.imbalance_ratio import imbalance_ratio


class TestImbalanceRatioBasicCases:
    """Test basic expected behavior of imbalance_ratio."""

    def test_equal_volumes_returns_zero(self) -> None:
        """R6: When bid and ask volumes are equal, ratio should be 0.0."""
        result = imbalance_ratio(bid_volume=100.0, ask_volume=100.0)
        assert result == pytest.approx(0.0)

    def test_all_bid_returns_positive_one(self) -> None:
        """R4: When ask volume is 0 and bid volume is positive, ratio should be 1.0."""
        result = imbalance_ratio(bid_volume=50.0, ask_volume=0.0)
        assert result == pytest.approx(1.0)

    def test_all_ask_returns_negative_one(self) -> None:
        """R5: When bid volume is 0 and ask volume is positive, ratio should be -1.0."""
        result = imbalance_ratio(bid_volume=0.0, ask_volume=50.0)
        assert result == pytest.approx(-1.0)

    def test_zero_volumes_returns_zero(self) -> None:
        """R2: When both bid and ask volumes are 0, ratio should be 0.0 (avoid div by zero)."""
        result = imbalance_ratio(bid_volume=0.0, ask_volume=0.0)
        assert result == pytest.approx(0.0)


class TestImbalanceRatioFormula:
    """Test the core formula: (bid - ask) / (bid + ask)."""

    def test_more_bid_than_ask_returns_positive(self) -> None:
        """R1, R3: When bid > ask, ratio should be positive."""
        # bid=150, ask=50 -> (150-50)/(150+50) = 100/200 = 0.5
        result = imbalance_ratio(bid_volume=150.0, ask_volume=50.0)
        assert result == pytest.approx(0.5)
        assert result > 0.0

    def test_more_ask_than_bid_returns_negative(self) -> None:
        """R1, R3: When ask > bid, ratio should be negative."""
        # bid=50, ask=150 -> (50-150)/(50+150) = -100/200 = -0.5
        result = imbalance_ratio(bid_volume=50.0, ask_volume=150.0)
        assert result == pytest.approx(-0.5)
        assert result < 0.0

    def test_formula_correctness_with_arbitrary_values(self) -> None:
        """R1: Verify formula with specific values."""
        # bid=75, ask=25 -> (75-25)/(75+25) = 50/100 = 0.5
        result = imbalance_ratio(bid_volume=75.0, ask_volume=25.0)
        expected = (75.0 - 25.0) / (75.0 + 25.0)
        assert result == pytest.approx(expected)


class TestImbalanceRatioBounds:
    """Test that result is always within [-1.0, 1.0] for valid inputs."""

    @pytest.mark.parametrize(
        "bid_volume,ask_volume",
        [
            (100.0, 0.0),      # all bid -> 1.0
            (0.0, 100.0),      # all ask -> -1.0
            (100.0, 100.0),    # equal -> 0.0
            (99.0, 1.0),       # mostly bid -> near 1.0
            (1.0, 99.0),       # mostly ask -> near -1.0
            (1000000.0, 1.0),  # extreme bid dominance
            (1.0, 1000000.0),  # extreme ask dominance
            (0.001, 0.001),    # tiny equal volumes
            (0.0, 0.0),        # zero volumes
        ],
    )
    def test_result_within_bounds(self, bid_volume: float, ask_volume: float) -> None:
        """R3: Result should always be in [-1.0, 1.0] for non-negative inputs."""
        result = imbalance_ratio(bid_volume=bid_volume, ask_volume=ask_volume)
        assert -1.0 <= result <= 1.0


class TestImbalanceRatioFloatPrecision:
    """Test behavior with small and large floating point values."""

    def test_small_volumes(self) -> None:
        """R1: Function should handle small floating point values correctly."""
        # Very small volumes should still compute correctly
        result = imbalance_ratio(bid_volume=0.0001, ask_volume=0.0003)
        # (0.0001 - 0.0003) / (0.0001 + 0.0003) = -0.0002 / 0.0004 = -0.5
        assert result == pytest.approx(-0.5)

    def test_very_small_volumes_near_zero(self) -> None:
        """R1: Function should handle very small volumes without precision issues."""
        result = imbalance_ratio(bid_volume=1e-10, ask_volume=1e-10)
        assert result == pytest.approx(0.0)

    def test_large_volumes(self) -> None:
        """R1: Function should handle large floating point values without overflow."""
        # Large volumes typical in crypto markets (high-volume orderbooks)
        result = imbalance_ratio(bid_volume=1e15, ask_volume=1e15)
        assert result == pytest.approx(0.0)

    def test_large_volumes_unequal(self) -> None:
        """R1: Function should handle large unequal volumes correctly."""
        # bid=3e15, ask=1e15 -> (3e15 - 1e15)/(3e15 + 1e15) = 2e15/4e15 = 0.5
        result = imbalance_ratio(bid_volume=3e15, ask_volume=1e15)
        assert result == pytest.approx(0.5)

    def test_mixed_small_and_large_volumes(self) -> None:
        """R1: Function should handle mix of small and large values."""
        # This tests numerical stability
        result = imbalance_ratio(bid_volume=1e10, ask_volume=1.0)
        # Should be very close to 1.0 but not exactly 1.0
        assert result == pytest.approx(1.0, rel=1e-9)
        assert result < 1.0


class TestImbalanceRatioSymmetry:
    """Test mathematical symmetry properties of the imbalance ratio."""

    def test_swapping_bid_ask_negates_result(self) -> None:
        """Swapping bid and ask should negate the result."""
        result1 = imbalance_ratio(bid_volume=120.0, ask_volume=80.0)
        result2 = imbalance_ratio(bid_volume=80.0, ask_volume=120.0)
        assert result1 == pytest.approx(-result2)

    def test_scaling_preserves_ratio(self) -> None:
        """Scaling both volumes by the same factor should not change the ratio."""
        result1 = imbalance_ratio(bid_volume=100.0, ask_volume=50.0)
        result2 = imbalance_ratio(bid_volume=1000.0, ask_volume=500.0)
        result3 = imbalance_ratio(bid_volume=10.0, ask_volume=5.0)
        assert result1 == pytest.approx(result2)
        assert result1 == pytest.approx(result3)
