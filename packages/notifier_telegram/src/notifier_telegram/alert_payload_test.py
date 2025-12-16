"""Tests for AlertPayload dataclass.

AlertPayload is a frozen dataclass containing all data needed to format and send
an imbalance alert via a notification channel.

Requirements covered:
- R1: AlertPayload must store symbol, ratio, bid_volume, ask_volume, timestamp, threshold
- R2: AlertPayload must be immutable (frozen dataclass)
- R3: Empty symbol raises ValueError
- R4: Negative timestamp raises ValueError
- R5: All float fields accept valid numeric values including edge cases
"""

import pytest

from notifier_telegram.alert_payload import AlertPayload


class TestAlertPayloadConstruction:
    """Tests for valid AlertPayload construction."""

    def test_creates_payload_with_all_fields(self) -> None:
        """R1: AlertPayload stores all required fields correctly."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.45,
            bid_volume=150000.0,
            ask_volume=85000.0,
            timestamp=1702800000.123,
            threshold=0.35,
        )

        assert payload.symbol == "BTCUSDT"
        assert payload.ratio == 0.45
        assert payload.bid_volume == 150000.0
        assert payload.ask_volume == 85000.0
        assert payload.timestamp == 1702800000.123
        assert payload.threshold == 0.35

    def test_creates_payload_with_negative_ratio(self) -> None:
        """R1: AlertPayload accepts negative ratio (more asks than bids)."""
        payload = AlertPayload(
            symbol="ETHUSDT",
            ratio=-0.65,
            bid_volume=35000.0,
            ask_volume=100000.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload.ratio == -0.65

    def test_creates_payload_with_zero_ratio(self) -> None:
        """R1: AlertPayload accepts zero ratio (balanced book)."""
        payload = AlertPayload(
            symbol="DOTUSDT",
            ratio=0.0,
            bid_volume=50000.0,
            ask_volume=50000.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload.ratio == 0.0

    def test_creates_payload_with_extreme_positive_ratio(self) -> None:
        """R1: AlertPayload accepts ratio at +1.0 boundary."""
        payload = AlertPayload(
            symbol="SOLUSDT",
            ratio=1.0,
            bid_volume=100000.0,
            ask_volume=0.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload.ratio == 1.0

    def test_creates_payload_with_extreme_negative_ratio(self) -> None:
        """R1: AlertPayload accepts ratio at -1.0 boundary."""
        payload = AlertPayload(
            symbol="SOLUSDT",
            ratio=-1.0,
            bid_volume=0.0,
            ask_volume=100000.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload.ratio == -1.0

    def test_creates_payload_with_zero_volumes(self) -> None:
        """R1: AlertPayload accepts zero volumes."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.0,
            bid_volume=0.0,
            ask_volume=0.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload.bid_volume == 0.0
        assert payload.ask_volume == 0.0

    def test_creates_payload_with_large_volumes(self) -> None:
        """R1: AlertPayload handles large volume values."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=1e15,
            ask_volume=5e14,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload.bid_volume == 1e15
        assert payload.ask_volume == 5e14

    def test_creates_payload_with_small_threshold(self) -> None:
        """R1: AlertPayload accepts various threshold values."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.01,
        )

        assert payload.threshold == 0.01

    def test_creates_payload_with_zero_timestamp(self) -> None:
        """R1: AlertPayload accepts zero timestamp (epoch)."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=0.0,
            threshold=0.35,
        )

        assert payload.timestamp == 0.0


class TestAlertPayloadValidation:
    """Tests for AlertPayload input validation."""

    def test_rejects_empty_symbol(self) -> None:
        """R3: Empty symbol string raises ValueError."""
        with pytest.raises(ValueError, match="symbol"):
            AlertPayload(
                symbol="",
                ratio=0.5,
                bid_volume=100.0,
                ask_volume=50.0,
                timestamp=1702800000.0,
                threshold=0.35,
            )

    def test_rejects_whitespace_only_symbol(self) -> None:
        """R3: Whitespace-only symbol raises ValueError."""
        with pytest.raises(ValueError, match="symbol"):
            AlertPayload(
                symbol="   ",
                ratio=0.5,
                bid_volume=100.0,
                ask_volume=50.0,
                timestamp=1702800000.0,
                threshold=0.35,
            )

    def test_rejects_tab_only_symbol(self) -> None:
        """R3: Tab-only symbol raises ValueError."""
        with pytest.raises(ValueError, match="symbol"):
            AlertPayload(
                symbol="\t\t",
                ratio=0.5,
                bid_volume=100.0,
                ask_volume=50.0,
                timestamp=1702800000.0,
                threshold=0.35,
            )

    def test_rejects_negative_timestamp(self) -> None:
        """R4: Negative timestamp raises ValueError."""
        with pytest.raises(ValueError, match="timestamp"):
            AlertPayload(
                symbol="BTCUSDT",
                ratio=0.5,
                bid_volume=100.0,
                ask_volume=50.0,
                timestamp=-1.0,
                threshold=0.35,
            )

    def test_rejects_very_negative_timestamp(self) -> None:
        """R4: Very negative timestamp raises ValueError."""
        with pytest.raises(ValueError, match="timestamp"):
            AlertPayload(
                symbol="BTCUSDT",
                ratio=0.5,
                bid_volume=100.0,
                ask_volume=50.0,
                timestamp=-999999999.0,
                threshold=0.35,
            )


class TestAlertPayloadImmutability:
    """Tests for AlertPayload immutability (frozen dataclass)."""

    def test_cannot_modify_symbol(self) -> None:
        """R2: Symbol attribute cannot be modified after creation."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        with pytest.raises(AttributeError):
            payload.symbol = "ETHUSDT"  # type: ignore[misc]

    def test_cannot_modify_ratio(self) -> None:
        """R2: Ratio attribute cannot be modified after creation."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        with pytest.raises(AttributeError):
            payload.ratio = 0.9  # type: ignore[misc]

    def test_cannot_modify_bid_volume(self) -> None:
        """R2: Bid volume attribute cannot be modified after creation."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        with pytest.raises(AttributeError):
            payload.bid_volume = 200.0  # type: ignore[misc]

    def test_cannot_modify_ask_volume(self) -> None:
        """R2: Ask volume attribute cannot be modified after creation."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        with pytest.raises(AttributeError):
            payload.ask_volume = 200.0  # type: ignore[misc]

    def test_cannot_modify_timestamp(self) -> None:
        """R2: Timestamp attribute cannot be modified after creation."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        with pytest.raises(AttributeError):
            payload.timestamp = 1702900000.0  # type: ignore[misc]

    def test_cannot_modify_threshold(self) -> None:
        """R2: Threshold attribute cannot be modified after creation."""
        payload = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        with pytest.raises(AttributeError):
            payload.threshold = 0.5  # type: ignore[misc]


class TestAlertPayloadEquality:
    """Tests for AlertPayload equality comparison."""

    def test_equal_payloads_are_equal(self) -> None:
        """Payloads with identical fields are equal."""
        payload1 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )
        payload2 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload1 == payload2

    def test_different_symbol_not_equal(self) -> None:
        """Payloads with different symbols are not equal."""
        payload1 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )
        payload2 = AlertPayload(
            symbol="ETHUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload1 != payload2

    def test_different_ratio_not_equal(self) -> None:
        """Payloads with different ratios are not equal."""
        payload1 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )
        payload2 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.6,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )

        assert payload1 != payload2

    def test_different_timestamp_not_equal(self) -> None:
        """Payloads with different timestamps are not equal."""
        payload1 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )
        payload2 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702900000.0,
            threshold=0.35,
        )

        assert payload1 != payload2

    def test_different_threshold_not_equal(self) -> None:
        """Payloads with different thresholds are not equal."""
        payload1 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.35,
        )
        payload2 = AlertPayload(
            symbol="BTCUSDT",
            ratio=0.5,
            bid_volume=100.0,
            ask_volume=50.0,
            timestamp=1702800000.0,
            threshold=0.50,
        )

        assert payload1 != payload2
