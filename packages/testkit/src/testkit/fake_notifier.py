"""Fake notifier implementation for testing.

This module provides a simple fake notifier for testing notification flows.
For tests that use AlertPayload (the real notifier protocol), use
FakeAlertNotifier from orderbook_watcher.testing instead.
"""


class FakeNotifier:
    """A test double for notification systems.

    Records all notifications for inspection during tests.
    Can be configured to raise errors for testing error handling.

    Note:
        This notifier uses a simple (symbol, ratio, message) signature.
        For tests that need the full AlertPayload protocol, use
        FakeAlertNotifier from orderbook_watcher.testing.
    """

    def __init__(self) -> None:
        """Initialize an empty notifier."""
        self._calls: list[tuple[str, float, str]] = []
        self._error_to_raise: Exception | None = None

    @property
    def call_count(self) -> int:
        """Number of times notify was called."""
        return len(self._calls)

    @property
    def last_message(self) -> str | None:
        """The message from the most recent notification, or None if no calls."""
        if not self._calls:
            return None
        return self._calls[-1][2]

    @property
    def last_call(self) -> tuple[str, float, str] | None:
        """The most recent notification as (symbol, ratio, message), or None."""
        if not self._calls:
            return None
        return self._calls[-1]

    @property
    def messages(self) -> list[str]:
        """All notification messages in chronological order."""
        return [call[2] for call in self._calls]

    @property
    def calls(self) -> list[tuple[str, float, str]]:
        """All notifications as (symbol, ratio, message) tuples."""
        return self._calls.copy()

    async def notify(self, symbol: str, ratio: float, message: str) -> None:
        """Record a notification and optionally raise a configured error.

        Args:
            symbol: The symbol being notified about.
            ratio: The imbalance ratio.
            message: The notification message.

        Raises:
            Exception: If configured via set_error().
        """
        self._calls.append((symbol, ratio, message))
        if self._error_to_raise is not None:
            raise self._error_to_raise

    def was_notified(self, symbol: str) -> bool:
        """Check if the given symbol was notified.

        Args:
            symbol: The symbol to check.

        Returns:
            True if any notification was sent for this symbol.
        """
        return any(call[0] == symbol for call in self._calls)

    def get_calls_for_symbol(self, symbol: str) -> list[tuple[str, float, str]]:
        """Get all notifications for a specific symbol.

        Args:
            symbol: The symbol to filter by.

        Returns:
            List of (symbol, ratio, message) tuples for the given symbol.
        """
        return [call for call in self._calls if call[0] == symbol]

    def reset(self) -> None:
        """Clear all recorded notifications and errors."""
        self._calls.clear()
        self._error_to_raise = None

    def set_error(self, error: Exception) -> None:
        """Configure the notifier to raise an error after recording.

        Args:
            error: The exception to raise on next notify() call.
        """
        self._error_to_raise = error

    def clear_error(self) -> None:
        """Clear any configured error."""
        self._error_to_raise = None
