"""Notifier protocol definition.

The Notifier protocol defines the abstract interface for notification channels.
Any implementation (Telegram, Slack, email, etc.) must conform to this protocol.
"""

from typing import Protocol, runtime_checkable

from notifier_telegram.alert_payload import AlertPayload


@runtime_checkable
class Notifier(Protocol):
    """Protocol for notification channel implementations.

    This protocol enables dependency injection and duck typing for notifiers.
    Implementations must provide an async send_alert method.
    """

    async def send_alert(self, alert: AlertPayload) -> None:
        """Send an imbalance alert.

        Args:
            alert: The alert payload containing all data for the notification.

        Raises:
            PermanentNotifierError: For non-retryable errors (e.g., 4xx HTTP).
            TransientNotifierError: For retryable errors (e.g., 5xx HTTP, network).
        """
        ...
