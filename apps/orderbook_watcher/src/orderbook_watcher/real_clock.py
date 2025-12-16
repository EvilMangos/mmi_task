"""RealClock implementation for production use.

RealClock is a production implementation of the Clock protocol
that returns actual system time in UTC.
"""

from datetime import datetime, timezone


class RealClock:
    """Production clock implementation that returns actual UTC time.

    Implements the Clock protocol from testkit for dependency injection.
    """

    def now(self) -> datetime:
        """Return the current datetime in UTC.

        Returns:
            Current datetime with UTC timezone.
        """
        return datetime.now(timezone.utc)
