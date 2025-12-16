"""Notifier protocols and exceptions.

This module defines the abstract interfaces for notification channels.
Any implementation (Telegram, Slack, email, etc.) must conform to these protocols.
"""

from typing import Protocol, runtime_checkable


class AlertPayload(Protocol):
    """Protocol for alert payload data structure.

    Defines the expected attributes for alert data passed to notifiers.
    Implementations may use dataclasses, named tuples, or any class
    that provides these attributes.

    Attributes:
        symbol: Trading pair symbol (e.g., "BTCUSDT").
        ratio: Computed imbalance ratio, range [-1.0, 1.0].
        bid_volume: Total bid volume for top N levels.
        ask_volume: Total ask volume for top N levels.
        timestamp: Unix timestamp (seconds since epoch).
        threshold: The threshold that was exceeded to trigger this alert.
    """

    @property
    def symbol(self) -> str:
        """Trading pair symbol."""
        ...

    @property
    def ratio(self) -> float:
        """Computed imbalance ratio."""
        ...

    @property
    def bid_volume(self) -> float:
        """Total bid volume for top N levels."""
        ...

    @property
    def ask_volume(self) -> float:
        """Total ask volume for top N levels."""
        ...

    @property
    def timestamp(self) -> float:
        """Unix timestamp (seconds since epoch)."""
        ...

    @property
    def threshold(self) -> float:
        """The threshold that was exceeded to trigger this alert."""
        ...


class NotifierError(Exception):
    """Base exception for notifier errors."""


class TransientNotifierError(NotifierError):
    """Transient error that may be retried.

    Raised for recoverable errors such as network timeouts,
    rate limiting, or temporary service unavailability.
    """


class PermanentNotifierError(NotifierError):
    """Permanent error that should not be retried.

    Raised for non-recoverable errors such as invalid credentials,
    malformed requests, or permanent service rejection (4xx HTTP).
    """


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
