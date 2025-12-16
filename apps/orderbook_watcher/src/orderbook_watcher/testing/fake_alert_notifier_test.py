"""Unit tests for FakeAlertNotifier test utility."""

import pytest
from notifier_telegram import (
    AlertPayload,
    PermanentNotifierError,
    TransientNotifierError,
)

from orderbook_watcher.testing import FakeAlertNotifier


def _make_alert(symbol: str = "BTCUSDT", ratio: float = 0.5) -> AlertPayload:
    """Create a test AlertPayload."""
    return AlertPayload(
        symbol=symbol,
        ratio=ratio,
        bid_volume=8.0,
        ask_volume=2.0,
        timestamp=1705320000.0,
        threshold=0.35,
    )


class TestFakeAlertNotifier:
    """Tests for FakeAlertNotifier test double."""

    @pytest.mark.asyncio
    async def test_records_calls(self) -> None:
        """FakeAlertNotifier records send_alert calls."""
        notifier = FakeAlertNotifier()
        alert = _make_alert()

        await notifier.send_alert(alert)

        assert notifier.call_count == 1
        assert notifier.last_call == alert

    @pytest.mark.asyncio
    async def test_multiple_calls_recorded_in_order(self) -> None:
        """Multiple calls are recorded in chronological order."""
        notifier = FakeAlertNotifier()
        alert1 = _make_alert("BTCUSDT")
        alert2 = _make_alert("ETHUSDT")

        await notifier.send_alert(alert1)
        await notifier.send_alert(alert2)

        assert notifier.call_count == 2
        assert notifier.calls == [alert1, alert2]
        assert notifier.last_call == alert2

    @pytest.mark.asyncio
    async def test_was_called_for_symbol(self) -> None:
        """was_called_for_symbol returns True for notified symbols."""
        notifier = FakeAlertNotifier()
        await notifier.send_alert(_make_alert("BTCUSDT"))

        assert notifier.was_called_for_symbol("BTCUSDT") is True
        assert notifier.was_called_for_symbol("ETHUSDT") is False

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol(self) -> None:
        """get_calls_for_symbol filters by symbol."""
        notifier = FakeAlertNotifier()
        btc1 = _make_alert("BTCUSDT", 0.4)
        eth = _make_alert("ETHUSDT", 0.5)
        btc2 = _make_alert("BTCUSDT", 0.6)

        await notifier.send_alert(btc1)
        await notifier.send_alert(eth)
        await notifier.send_alert(btc2)

        btc_calls = notifier.get_calls_for_symbol("BTCUSDT")
        assert btc_calls == [btc1, btc2]

    @pytest.mark.asyncio
    async def test_set_transient_error(self) -> None:
        """set_transient_error causes send_alert to raise TransientNotifierError."""
        notifier = FakeAlertNotifier()
        notifier.set_transient_error("Network error")

        with pytest.raises(TransientNotifierError, match="Network error"):
            await notifier.send_alert(_make_alert())

        # Call was still recorded before error
        assert notifier.call_count == 1

    @pytest.mark.asyncio
    async def test_set_permanent_error(self) -> None:
        """set_permanent_error causes send_alert to raise PermanentNotifierError."""
        notifier = FakeAlertNotifier()
        notifier.set_permanent_error("Invalid config")

        with pytest.raises(PermanentNotifierError, match="Invalid config"):
            await notifier.send_alert(_make_alert())

        # Call was still recorded before error
        assert notifier.call_count == 1

    @pytest.mark.asyncio
    async def test_clear_error(self) -> None:
        """clear_error removes configured error."""
        notifier = FakeAlertNotifier()
        notifier.set_transient_error("Error")
        notifier.clear_error()

        # Should not raise
        await notifier.send_alert(_make_alert())
        assert notifier.call_count == 1

    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        """reset clears all recorded calls and errors."""
        notifier = FakeAlertNotifier()
        notifier.set_transient_error("Error")
        with pytest.raises(TransientNotifierError):
            await notifier.send_alert(_make_alert())  # This will raise but record

        notifier.reset()

        assert notifier.call_count == 0
        assert notifier.last_call is None
        # Error should also be cleared
        await notifier.send_alert(_make_alert())  # Should not raise
        assert notifier.call_count == 1

    def test_empty_notifier(self) -> None:
        """Empty notifier has expected initial state."""
        notifier = FakeAlertNotifier()

        assert notifier.call_count == 0
        assert notifier.last_call is None
        assert notifier.calls == []
        assert notifier.was_called_for_symbol("ANY") is False
