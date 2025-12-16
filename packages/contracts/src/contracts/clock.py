"""Clock protocol for time abstraction."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Protocol for time sources.

    Allows injection of deterministic time sources for testing
    while using real time in production.
    """

    def now(self) -> datetime:
        """Return the current datetime.

        Returns:
            The current datetime.
        """
        ...
