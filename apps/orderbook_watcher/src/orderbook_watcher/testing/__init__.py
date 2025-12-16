"""Test utilities for orderbook_watcher tests."""

from notifier_telegram import (
    AlertPayload,
    PermanentNotifierError,
    TransientNotifierError,
)


class FakeAlertNotifier:
    """A test double for the Notifier protocol.

    Records all send_alert calls for inspection during tests.
    Can be configured to raise errors for testing error handling.
    """

    def __init__(self) -> None:
        """Initialize an empty notifier."""
        self._calls: list[AlertPayload] = []
        self._error_to_raise: Exception | None = None

    @property
    def call_count(self) -> int:
        """Number of times send_alert was called."""
        return len(self._calls)

    @property
    def calls(self) -> list[AlertPayload]:
        """All recorded AlertPayload objects in chronological order."""
        return self._calls.copy()

    @property
    def last_call(self) -> AlertPayload | None:
        """The most recent AlertPayload, or None if no calls."""
        if not self._calls:
            return None
        return self._calls[-1]

    async def send_alert(self, alert: AlertPayload) -> None:
        """Record an alert and optionally raise a configured error.

        Args:
            alert: The alert payload to record.

        Raises:
            Exception: If configured via set_error_to_raise().
        """
        self._calls.append(alert)
        if self._error_to_raise is not None:
            raise self._error_to_raise

    def set_transient_error(self, message: str = "Transient error") -> None:
        """Configure the notifier to raise a TransientNotifierError.

        Args:
            message: Error message to use.
        """
        self._error_to_raise = TransientNotifierError(message)

    def set_permanent_error(self, message: str = "Permanent error") -> None:
        """Configure the notifier to raise a PermanentNotifierError.

        Args:
            message: Error message to use.
        """
        self._error_to_raise = PermanentNotifierError(message)

    def clear_error(self) -> None:
        """Clear any configured error."""
        self._error_to_raise = None

    def was_called_for_symbol(self, symbol: str) -> bool:
        """Check if send_alert was called for the given symbol.

        Args:
            symbol: The symbol to check.

        Returns:
            True if any alert was recorded for this symbol.
        """
        return any(call.symbol == symbol for call in self._calls)

    def get_calls_for_symbol(self, symbol: str) -> list[AlertPayload]:
        """Get all alerts for a specific symbol.

        Args:
            symbol: The symbol to filter by.

        Returns:
            List of AlertPayload objects for the given symbol.
        """
        return [call for call in self._calls if call.symbol == symbol]

    def reset(self) -> None:
        """Clear all recorded calls and errors."""
        self._calls.clear()
        self._error_to_raise = None


__all__ = ["FakeAlertNotifier"]
