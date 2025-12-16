"""Fake notifier implementation for testing."""


class FakeNotifier:
    """A test double for notification systems.

    Records all notifications for inspection during tests.
    """

    def __init__(self) -> None:
        """Initialize an empty notifier."""
        self._calls: list[tuple[str, float, str]] = []

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
        """Record a notification.

        Args:
            symbol: The symbol being notified about.
            ratio: The imbalance ratio.
            message: The notification message.
        """
        self._calls.append((symbol, ratio, message))

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
        """Clear all recorded notifications."""
        self._calls.clear()
