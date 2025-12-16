"""Tests for Notifier protocol definition.

The Notifier protocol defines the abstract interface for notification channels.
Any implementation (Telegram, Slack, email, etc.) must conform to this protocol.

Requirements covered:
- R1: Notifier is defined as a Protocol class
- R2: Protocol defines async send_alert method accepting AlertPayload
- R3: send_alert has return type None (or nothing)
- R4: Classes implementing the method are recognized as Notifier
- R5: Protocol enables dependency injection/duck typing
"""

import asyncio

import pytest

from notifier_telegram.alert_payload import AlertPayload
from contracts import Notifier
from notifier_telegram.testing import make_payload


class TestNotifierProtocolDefinition:
    """Tests for Notifier protocol structure."""

    def test_notifier_is_protocol(self) -> None:
        """R1: Notifier is defined using typing.Protocol."""
        from typing_extensions import is_protocol

        assert is_protocol(Notifier)

    def test_notifier_has_send_alert(self) -> None:
        """R2: Notifier protocol declares send_alert method."""
        assert hasattr(Notifier, "send_alert")

    def test_notifier_is_runtime_checkable(self) -> None:
        """R4: Notifier can be used with isinstance() at runtime."""

        # This test verifies @runtime_checkable decorator is applied
        # If not runtime_checkable, isinstance() would raise TypeError
        class FakeNotifier:
            async def send_alert(self, alert: AlertPayload) -> None:
                pass

        fake = FakeNotifier()
        # This should not raise TypeError
        result = isinstance(fake, Notifier)
        assert result is True


class TestNotifierProtocolCompliance:
    """Tests for protocol compliance checking."""

    def test_class_with_matching_signature_is_notifier(self) -> None:
        """R4: Class with matching send_alert signature is recognized as Notifier."""

        class MatchingNotifier:
            async def send_alert(self, alert: AlertPayload) -> None:
                pass

        notifier = MatchingNotifier()
        assert isinstance(notifier, Notifier)

    def test_class_without_send_alert_is_not_notifier(self) -> None:
        """R4: Class without send_alert is not a Notifier."""

        class MissingMethod:
            pass

        obj = MissingMethod()
        assert not isinstance(obj, Notifier)

    def test_class_with_sync_send_alert_is_recognized(self) -> None:
        """Protocol check doesn't distinguish sync/async at runtime with isinstance.

        Note: At static type checking time, the async signature would be enforced.
        This test documents runtime behavior with @runtime_checkable.
        """

        class SyncNotifier:
            def send_alert(self, alert: AlertPayload) -> None:  # sync, not async
                pass

        # isinstance only checks for method existence, not async-ness
        notifier = SyncNotifier()
        # This will pass because runtime_checkable only checks attribute existence
        assert isinstance(notifier, Notifier)

    def test_class_with_wrong_param_name_is_still_recognized(self) -> None:
        """Protocol runtime check only verifies method existence, not signature details.

        Note: Type checkers would catch signature mismatches at static analysis time.
        """

        class WrongParamName:
            async def send_alert(
                self, payload: AlertPayload
            ) -> None:  # 'payload' not 'alert'
                pass

        obj = WrongParamName()
        # isinstance with @runtime_checkable only checks method existence
        assert isinstance(obj, Notifier)


@pytest.mark.asyncio
class TestNotifierProtocolUsage:
    """Tests for using Notifier protocol in dependency injection patterns."""

    async def test_can_call_send_alert_on_implementation(self) -> None:
        """R5: Can call send_alert through Notifier-typed variable."""
        received_alerts: list[AlertPayload] = []

        class RecordingNotifier:
            async def send_alert(self, alert: AlertPayload) -> None:
                received_alerts.append(alert)

        # Use as Notifier type (duck typing)
        notifier: Notifier = RecordingNotifier()
        payload = make_payload()

        await notifier.send_alert(payload)

        assert len(received_alerts) == 1
        assert received_alerts[0] is payload

    async def test_multiple_implementations_interchangeable(self) -> None:
        """R5: Different implementations can be swapped via Notifier interface."""
        call_log: list[str] = []

        class NotifierA:
            async def send_alert(self, alert: AlertPayload) -> None:
                call_log.append("A")

        class NotifierB:
            async def send_alert(self, alert: AlertPayload) -> None:
                call_log.append("B")

        payload = make_payload()

        # Both can be used as Notifier
        notifiers: list[Notifier] = [NotifierA(), NotifierB()]

        for notifier in notifiers:
            await notifier.send_alert(payload)

        assert call_log == ["A", "B"]

    async def test_can_create_wrapper_around_notifier(self) -> None:
        """R5: Can create decorator/wrapper that takes Notifier."""
        inner_calls: list[AlertPayload] = []

        class InnerNotifier:
            async def send_alert(self, alert: AlertPayload) -> None:
                inner_calls.append(alert)

        class LoggingNotifierWrapper:
            def __init__(self, wrapped: Notifier) -> None:
                self._wrapped = wrapped
                self.logged: list[str] = []

            async def send_alert(self, alert: AlertPayload) -> None:
                self.logged.append(f"Sending alert for {alert.symbol}")
                await self._wrapped.send_alert(alert)

        inner = InnerNotifier()
        wrapper = LoggingNotifierWrapper(inner)
        payload = make_payload(symbol="ETHUSDT")

        await wrapper.send_alert(payload)

        assert len(inner_calls) == 1
        assert wrapper.logged == ["Sending alert for ETHUSDT"]


@pytest.mark.asyncio
class TestNotifierProtocolAsync:
    """Tests verifying async behavior expectations."""

    async def test_send_alert_returns_awaitable(self) -> None:
        """R2, R3: send_alert should return something awaitable."""

        class AsyncNotifier:
            async def send_alert(self, alert: AlertPayload) -> None:
                pass

        notifier = AsyncNotifier()
        payload = make_payload()

        result = notifier.send_alert(payload)

        # Should be a coroutine
        assert asyncio.iscoroutine(result)

        # Clean up - await it
        await result

    async def test_send_alert_can_be_used_with_asyncio_gather(self) -> None:
        """R2: Multiple send_alert calls can be gathered concurrently."""
        call_times: list[float] = []
        import time

        class SlowNotifier:
            async def send_alert(self, alert: AlertPayload) -> None:
                await asyncio.sleep(0.01)  # Small delay
                call_times.append(time.time())

        notifier = SlowNotifier()
        payloads = [make_payload(symbol=f"SYM{i}") for i in range(3)]

        # Gather all calls
        await asyncio.gather(*[notifier.send_alert(p) for p in payloads])

        assert len(call_times) == 3
