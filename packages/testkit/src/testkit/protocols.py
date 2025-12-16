"""Protocol definitions for testing."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    """Protocol for notification systems."""

    async def notify(self, symbol: str, ratio: float, message: str) -> None:
        """Send a notification for a symbol with the given imbalance ratio and message."""
        ...
