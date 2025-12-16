"""Tests for FakeNotifier - a test double for notification systems."""

import pytest

from testkit.fake_notifier import FakeNotifier


class TestFakeNotifierInitialization:
    """Test FakeNotifier initialization and initial state."""

    def test_creates_with_empty_state(self):
        notifier = FakeNotifier()

        assert notifier.call_count == 0
        assert notifier.last_message is None
        assert notifier.last_call is None
        assert notifier.messages == []
        assert notifier.calls == []

    def test_has_all_required_attributes(self):
        notifier = FakeNotifier()

        assert hasattr(notifier, "call_count")
        assert hasattr(notifier, "last_message")
        assert hasattr(notifier, "last_call")
        assert hasattr(notifier, "messages")
        assert hasattr(notifier, "calls")


class TestFakeNotifierNotify:
    """Test the notify method and state recording."""

    @pytest.mark.asyncio
    async def test_notify_records_single_call(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Test alert")

        assert notifier.call_count == 1
        assert notifier.last_message == "Test alert"
        assert notifier.last_call == ("BTCUSDT", 0.5, "Test alert")
        assert notifier.messages == ["Test alert"]
        assert notifier.calls == [("BTCUSDT", 0.5, "Test alert")]

    @pytest.mark.asyncio
    async def test_notify_records_multiple_calls(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert 1")
        await notifier.notify(symbol="DOTUSDT", ratio=0.3, message="Alert 2")
        await notifier.notify(symbol="SOLUSDT", ratio=0.7, message="Alert 3")

        assert notifier.call_count == 3
        assert notifier.last_message == "Alert 3"
        assert notifier.last_call == ("SOLUSDT", 0.7, "Alert 3")
        assert notifier.messages == ["Alert 1", "Alert 2", "Alert 3"]
        assert notifier.calls == [
            ("BTCUSDT", 0.5, "Alert 1"),
            ("DOTUSDT", 0.3, "Alert 2"),
            ("SOLUSDT", 0.7, "Alert 3"),
        ]

    @pytest.mark.asyncio
    async def test_notify_with_negative_ratio(self):
        notifier = FakeNotifier()

        await notifier.notify(
            symbol="BTCUSDT", ratio=-0.3, message="Negative imbalance"
        )

        assert notifier.call_count == 1
        assert notifier.last_call == ("BTCUSDT", -0.3, "Negative imbalance")

    @pytest.mark.asyncio
    async def test_notify_with_zero_ratio(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.0, message="Balanced")

        assert notifier.call_count == 1
        assert notifier.last_call == ("BTCUSDT", 0.0, "Balanced")

    @pytest.mark.asyncio
    async def test_notify_with_extreme_ratio(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=1.0, message="All bids")

        assert notifier.call_count == 1
        assert notifier.last_call == ("BTCUSDT", 1.0, "All bids")

    @pytest.mark.asyncio
    async def test_notify_with_empty_message(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="")

        assert notifier.call_count == 1
        assert notifier.last_message == ""
        assert notifier.messages == [""]

    @pytest.mark.asyncio
    async def test_notify_with_multiline_message(self):
        notifier = FakeNotifier()
        message = "Line 1\nLine 2\nLine 3"

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message=message)

        assert notifier.last_message == message
        assert notifier.messages == [message]

    @pytest.mark.asyncio
    async def test_notify_preserves_call_order(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="A", ratio=0.1, message="First")
        await notifier.notify(symbol="B", ratio=0.2, message="Second")
        await notifier.notify(symbol="C", ratio=0.3, message="Third")
        await notifier.notify(symbol="D", ratio=0.4, message="Fourth")

        assert [call[0] for call in notifier.calls] == ["A", "B", "C", "D"]
        assert [call[2] for call in notifier.calls] == [
            "First",
            "Second",
            "Third",
            "Fourth",
        ]


class TestFakeNotifierWasNotified:
    """Test symbol-specific notification checking."""

    @pytest.mark.asyncio
    async def test_was_notified_returns_false_when_no_calls(self):
        notifier = FakeNotifier()

        assert notifier.was_notified(symbol="BTCUSDT") is False

    @pytest.mark.asyncio
    async def test_was_notified_returns_true_when_symbol_called(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert")

        assert notifier.was_notified(symbol="BTCUSDT") is True

    @pytest.mark.asyncio
    async def test_was_notified_returns_false_for_different_symbol(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert")

        assert notifier.was_notified(symbol="DOTUSDT") is False

    @pytest.mark.asyncio
    async def test_was_notified_with_multiple_symbols(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert 1")
        await notifier.notify(symbol="DOTUSDT", ratio=0.3, message="Alert 2")

        assert notifier.was_notified(symbol="BTCUSDT") is True
        assert notifier.was_notified(symbol="DOTUSDT") is True
        assert notifier.was_notified(symbol="SOLUSDT") is False

    @pytest.mark.asyncio
    async def test_was_notified_is_case_sensitive(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert")

        assert notifier.was_notified(symbol="BTCUSDT") is True
        assert notifier.was_notified(symbol="btcusdt") is False


class TestFakeNotifierGetCallsForSymbol:
    """Test retrieving calls for a specific symbol."""

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol_returns_empty_list_when_no_calls(self):
        notifier = FakeNotifier()

        calls = notifier.get_calls_for_symbol("BTCUSDT")

        assert calls == []

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol_returns_matching_calls(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert 1")
        await notifier.notify(symbol="BTCUSDT", ratio=0.6, message="Alert 2")

        calls = notifier.get_calls_for_symbol("BTCUSDT")

        assert len(calls) == 2
        assert calls == [
            ("BTCUSDT", 0.5, "Alert 1"),
            ("BTCUSDT", 0.6, "Alert 2"),
        ]

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol_filters_other_symbols(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="BTC Alert")
        await notifier.notify(symbol="DOTUSDT", ratio=0.3, message="DOT Alert")
        await notifier.notify(symbol="BTCUSDT", ratio=0.7, message="BTC Alert 2")

        calls = notifier.get_calls_for_symbol("BTCUSDT")

        assert len(calls) == 2
        assert calls == [
            ("BTCUSDT", 0.5, "BTC Alert"),
            ("BTCUSDT", 0.7, "BTC Alert 2"),
        ]

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol_returns_empty_for_unknown_symbol(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert")

        calls = notifier.get_calls_for_symbol("DOTUSDT")

        assert calls == []

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol_preserves_order(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.1, message="First")
        await notifier.notify(symbol="DOTUSDT", ratio=0.2, message="Other")
        await notifier.notify(symbol="BTCUSDT", ratio=0.3, message="Second")
        await notifier.notify(symbol="BTCUSDT", ratio=0.4, message="Third")

        calls = notifier.get_calls_for_symbol("BTCUSDT")

        assert [call[1] for call in calls] == [0.1, 0.3, 0.4]
        assert [call[2] for call in calls] == ["First", "Second", "Third"]


class TestFakeNotifierReset:
    """Test reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_clears_all_state(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert 1")
        await notifier.notify(symbol="DOTUSDT", ratio=0.3, message="Alert 2")

        notifier.reset()

        assert notifier.call_count == 0
        assert notifier.last_message is None
        assert notifier.last_call is None
        assert notifier.messages == []
        assert notifier.calls == []

    @pytest.mark.asyncio
    async def test_reset_allows_new_calls(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Before reset")
        notifier.reset()
        await notifier.notify(symbol="DOTUSDT", ratio=0.3, message="After reset")

        assert notifier.call_count == 1
        assert notifier.last_message == "After reset"
        assert notifier.calls == [("DOTUSDT", 0.3, "After reset")]

    @pytest.mark.asyncio
    async def test_reset_multiple_times_is_idempotent(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert")
        notifier.reset()
        notifier.reset()
        notifier.reset()

        assert notifier.call_count == 0
        assert notifier.calls == []

    def test_reset_on_fresh_notifier_is_safe(self):
        notifier = FakeNotifier()

        notifier.reset()

        assert notifier.call_count == 0
        assert notifier.messages == []


class TestFakeNotifierProtocolCompliance:
    """Test that FakeNotifier implements Notifier protocol correctly."""

    def test_has_notify_method(self):
        notifier = FakeNotifier()
        assert hasattr(notifier, "notify")
        assert callable(notifier.notify)

    @pytest.mark.asyncio
    async def test_notify_is_async(self):
        notifier = FakeNotifier()
        import inspect

        assert inspect.iscoroutinefunction(notifier.notify)

    @pytest.mark.asyncio
    async def test_notify_signature_matches_protocol(self):
        notifier = FakeNotifier()

        # Should accept symbol, ratio, message as keyword arguments
        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Test")

        # Should also work with positional arguments
        await notifier.notify("DOTUSDT", 0.3, "Test 2")


class TestFakeNotifierEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_notify_with_very_long_message(self):
        notifier = FakeNotifier()
        long_message = "A" * 10000

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message=long_message)

        assert notifier.last_message == long_message
        assert len(notifier.messages[0]) == 10000

    @pytest.mark.asyncio
    async def test_notify_with_special_characters_in_message(self):
        notifier = FakeNotifier()
        message = "Alert! 🚨 Price: $100.50 €95.00 \n\t Special chars: <>&'\""

        await notifier.notify(symbol="BTCUSDT", ratio=0.5, message=message)

        assert notifier.last_message == message

    @pytest.mark.asyncio
    async def test_notify_with_unicode_symbol(self):
        notifier = FakeNotifier()

        await notifier.notify(symbol="BTC₿USDT", ratio=0.5, message="Unicode symbol")

        assert notifier.was_notified(symbol="BTC₿USDT")

    @pytest.mark.asyncio
    async def test_many_notifications_performance(self):
        notifier = FakeNotifier()

        # Should handle many notifications efficiently
        for i in range(1000):
            await notifier.notify(symbol=f"SYMBOL{i}", ratio=0.5, message=f"Alert {i}")

        assert notifier.call_count == 1000
        assert len(notifier.calls) == 1000
        assert len(notifier.messages) == 1000

    @pytest.mark.asyncio
    async def test_get_calls_for_symbol_with_many_calls(self):
        notifier = FakeNotifier()

        for i in range(100):
            await notifier.notify(symbol="BTCUSDT", ratio=0.5, message=f"Alert {i}")

        calls = notifier.get_calls_for_symbol("BTCUSDT")

        assert len(calls) == 100
        assert all(call[0] == "BTCUSDT" for call in calls)
