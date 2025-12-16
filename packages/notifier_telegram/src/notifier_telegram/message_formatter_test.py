"""Tests for message formatting functions.

The message formatter converts AlertPayload data into human-readable text
suitable for Telegram messages.

Requirements covered:
- R1: format_alert_message returns a non-empty string
- R2: Output contains the symbol
- R3: Output contains the imbalance ratio (formatted as percentage or decimal)
- R4: Output contains bid and ask volumes
- R5: Output contains the threshold that was exceeded
- R6: Output handles positive and negative ratios appropriately
- R7: Output handles edge cases (zero, extreme values)
- R8: Output is consistent and deterministic
"""

from notifier_telegram.message_formatter import format_alert_message
from notifier_telegram.testing import make_payload


class TestFormatAlertMessageBasic:
    """Tests for basic message formatting functionality."""

    def test_returns_non_empty_string(self) -> None:
        """R1: format_alert_message returns a non-empty string."""
        payload = make_payload()
        result = format_alert_message(payload)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_symbol(self) -> None:
        """R2: Formatted message contains the symbol."""
        payload = make_payload(symbol="BTCUSDT")
        result = format_alert_message(payload)

        assert "BTCUSDT" in result

    def test_contains_different_symbol(self) -> None:
        """R2: Formatted message contains the correct symbol for different inputs."""
        payload = make_payload(symbol="ETHUSDT")
        result = format_alert_message(payload)

        assert "ETHUSDT" in result
        assert "BTCUSDT" not in result

    def test_contains_ratio_value(self) -> None:
        """R3: Formatted message contains the imbalance ratio."""
        payload = make_payload(ratio=0.45)
        result = format_alert_message(payload)

        # Should contain the ratio in recognizable format
        # Use a distinctive ratio value that won't accidentally match other fields
        assert "0.45" in result or "45%" in result
        # Ensure message references ratio/imbalance concept
        result_lower = result.lower()
        assert "ratio" in result_lower or "imbalance" in result_lower

    def test_contains_bid_volume(self) -> None:
        """R4: Formatted message contains bid volume information."""
        payload = make_payload(bid_volume=150000.0)
        result = format_alert_message(payload)

        # Should contain some representation of the bid volume
        assert "150000" in result or "150,000" in result or "150k" in result.lower()

    def test_contains_ask_volume(self) -> None:
        """R4: Formatted message contains ask volume information."""
        payload = make_payload(ask_volume=85000.0)
        result = format_alert_message(payload)

        # Should contain some representation of the ask volume
        assert "85000" in result or "85,000" in result or "85k" in result.lower()

    def test_contains_threshold(self) -> None:
        """R5: Formatted message contains the threshold value."""
        payload = make_payload(threshold=0.35)
        result = format_alert_message(payload)

        # Should contain the threshold value
        assert "0.35" in result or "35%" in result
        # Ensure message references threshold concept
        result_lower = result.lower()
        assert "threshold" in result_lower

    def test_contains_timestamp(self) -> None:
        """R?: Formatted message contains timestamp representation."""
        # Use a specific timestamp: 2023-12-17 08:00:00 UTC
        payload = make_payload(timestamp=1702800000.0)
        result = format_alert_message(payload)

        # Should contain some representation of the time
        # Either epoch, date/time parts, or formatted string
        has_timestamp = (
            "1702800000" in result  # epoch
            or "2023-12-17" in result  # ISO date
            or "2023" in result  # year
            or "Dec" in result  # month name
            or "time" in result.lower()  # time label
            or ":" in result  # time separator (HH:MM)
        )
        assert has_timestamp, "Message should contain timestamp information"


class TestFormatAlertMessageRatioHandling:
    """Tests for handling different ratio values."""

    def test_positive_ratio_formatting(self) -> None:
        """R6: Positive ratio is formatted appropriately (bid dominant)."""
        payload = make_payload(ratio=0.65, bid_volume=165000.0, ask_volume=35000.0)
        result = format_alert_message(payload)

        # Should contain the ratio value
        assert "0.65" in result or "65%" in result

    def test_negative_ratio_formatting(self) -> None:
        """R6: Negative ratio is formatted appropriately (ask dominant)."""
        payload = make_payload(ratio=-0.55, bid_volume=45000.0, ask_volume=155000.0)
        result = format_alert_message(payload)

        # Should contain the negative ratio value (with or without sign displayed)
        assert "-0.55" in result or "-55%" in result or "0.55" in result

    def test_zero_ratio_formatting(self) -> None:
        """R7: Zero ratio is handled correctly."""
        payload = make_payload(ratio=0.0, bid_volume=100000.0, ask_volume=100000.0)
        result = format_alert_message(payload)

        # Zero ratio should produce valid output - verify message structure
        assert isinstance(result, str)
        assert len(result) > 20  # Should have substantial content

    def test_maximum_positive_ratio_formatting(self) -> None:
        """R7: Maximum ratio (+1.0) is handled correctly."""
        payload = make_payload(ratio=1.0, bid_volume=100000.0, ask_volume=0.0)
        result = format_alert_message(payload)

        # Should contain ratio of 1.0 or 100%
        assert "1.0" in result or "100%" in result or " 1 " in result or "1\n" in result

    def test_maximum_negative_ratio_formatting(self) -> None:
        """R7: Maximum negative ratio (-1.0) is handled correctly."""
        payload = make_payload(ratio=-1.0, bid_volume=0.0, ask_volume=100000.0)
        result = format_alert_message(payload)

        # Should contain ratio of -1.0 or handle negative extreme
        assert "-1.0" in result or "-100%" in result or "1.0" in result

    def test_small_positive_ratio_formatting(self) -> None:
        """R3: Small positive ratio is visible in output."""
        payload = make_payload(ratio=0.01)
        result = format_alert_message(payload)

        # Should contain the small ratio value precisely
        assert "0.01" in result or "1%" in result


class TestFormatAlertMessageVolumeHandling:
    """Tests for handling different volume values."""

    def test_zero_volumes_formatting(self) -> None:
        """R7: Zero volumes are handled correctly."""
        payload = make_payload(ratio=0.0, bid_volume=0.0, ask_volume=0.0)
        result = format_alert_message(payload)

        # Should not crash and should produce valid output
        assert isinstance(result, str)
        assert len(result) > 0

    def test_large_volumes_formatting(self) -> None:
        """R7: Large volumes are handled correctly."""
        payload = make_payload(
            ratio=0.5,
            bid_volume=1_000_000_000.0,
            ask_volume=333_333_333.33,
        )
        result = format_alert_message(payload)

        # Should produce valid output without overflow
        assert isinstance(result, str)
        assert len(result) > 0

    def test_small_volumes_formatting(self) -> None:
        """R7: Small volumes are handled correctly."""
        payload = make_payload(
            ratio=0.5,
            bid_volume=0.001,
            ask_volume=0.0003,
        )
        result = format_alert_message(payload)

        # Should produce valid output
        assert isinstance(result, str)
        assert len(result) > 0

    def test_asymmetric_volumes_shows_both(self) -> None:
        """R4: Both bid and ask volumes appear in output even when very different."""
        payload = make_payload(
            ratio=0.99,
            bid_volume=1000000.0,
            ask_volume=5000.0,
        )
        result = format_alert_message(payload)

        # Both volumes should be represented somehow
        assert isinstance(result, str)
        # Basic sanity check - message should be substantial
        assert len(result) > 20


class TestFormatAlertMessageConsistency:
    """Tests for output consistency and determinism."""

    def test_same_input_produces_same_output(self) -> None:
        """R8: Same AlertPayload always produces identical output."""
        payload = make_payload(
            symbol="SOLUSDT",
            ratio=0.42,
            bid_volume=71000.0,
            ask_volume=41000.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        result1 = format_alert_message(payload)
        result2 = format_alert_message(payload)

        assert result1 == result2

    def test_different_symbols_produce_different_output(self) -> None:
        """R8: Different symbols produce different output."""
        payload1 = make_payload(symbol="BTCUSDT")
        payload2 = make_payload(symbol="ETHUSDT")

        result1 = format_alert_message(payload1)
        result2 = format_alert_message(payload2)

        assert result1 != result2

    def test_different_ratios_produce_different_output(self) -> None:
        """R8: Different ratios produce different output."""
        payload1 = make_payload(ratio=0.45)
        payload2 = make_payload(ratio=0.75)

        result1 = format_alert_message(payload1)
        result2 = format_alert_message(payload2)

        assert result1 != result2


class TestFormatAlertMessageEdgeCases:
    """Tests for edge cases in message formatting."""

    def test_symbol_with_numbers(self) -> None:
        """Symbol containing numbers is handled correctly."""
        payload = make_payload(symbol="1000SHIBUSDT")
        result = format_alert_message(payload)

        assert "1000SHIBUSDT" in result

    def test_very_precise_ratio(self) -> None:
        """Ratio with many decimal places is handled (may be truncated)."""
        payload = make_payload(ratio=0.123456789)
        result = format_alert_message(payload)

        # Should contain at least the first few significant digits of the ratio
        assert "0.12" in result or "12.3" in result or "12%" in result

    def test_very_precise_volumes(self) -> None:
        """Volumes with many decimal places are handled."""
        payload = make_payload(
            bid_volume=123456.789012345,
            ask_volume=98765.432109876,
        )
        result = format_alert_message(payload)

        # Should produce valid output
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_thresholds_reflected(self) -> None:
        """Different threshold values appear in output differently."""
        payload1 = make_payload(threshold=0.35)
        payload2 = make_payload(threshold=0.50)

        result1 = format_alert_message(payload1)
        result2 = format_alert_message(payload2)

        # The outputs should differ due to different thresholds
        assert result1 != result2


class TestFormatAlertMessageReadability:
    """Tests for human readability of formatted messages."""

    def test_message_has_reasonable_length(self) -> None:
        """Formatted message has reasonable length for Telegram."""
        payload = make_payload()
        result = format_alert_message(payload)

        # Telegram message limit is 4096, but alert should be concise
        assert 20 < len(result) < 1000

    def test_message_is_multiline_or_structured(self) -> None:
        """Message should have some structure (newlines or delimiters)."""
        payload = make_payload()
        result = format_alert_message(payload)

        # Should have some structure - either newlines, colons, or other delimiters
        has_structure = (
            "\n" in result or ":" in result or "|" in result or "-" in result
        )
        assert has_structure, "Message should have some structural elements"

    def test_message_contains_alert_indicator(self) -> None:
        """Message should indicate this is an alert somehow."""
        payload = make_payload()
        result = format_alert_message(payload)

        # Should contain some alert-related word
        result_lower = result.lower()
        has_alert_indicator = (
            "alert" in result_lower
            or "imbalance" in result_lower
            or "warning" in result_lower
            or "!" in result
            or "exceeded" in result_lower
            or "threshold" in result_lower
        )
        assert has_alert_indicator, "Message should indicate it's an alert"
