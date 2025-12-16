"""Protocol definitions for testing."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Protocol for time sources."""

    def now(self) -> datetime:
        """Return the current datetime."""
        ...


class Notifier(Protocol):
    """Protocol for notification systems."""

    async def notify(self, symbol: str, ratio: float, message: str) -> None:
        """Send a notification for a symbol with the given imbalance ratio and message."""
        ...
