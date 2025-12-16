"""Fake clock implementation for deterministic testing."""

from datetime import datetime, timedelta

from signal_engine.clock import Clock


class FakeClock(Clock):
    """A deterministic time source for testing.

    Allows advancing time manually and resetting to initial state.
    """

    def __init__(self, initial_time: datetime | None = None) -> None:
        """Initialize the clock with a specific time or epoch.

        Args:
            initial_time: Starting datetime. Defaults to epoch (1970-01-01 00:00:00).
        """
        if initial_time is None:
            initial_time = datetime(1970, 1, 1, 0, 0, 0)
        self._initial_time = initial_time
        self._current_time = initial_time

    def now(self) -> datetime:
        """Return the current time.

        Returns:
            Current datetime value.
        """
        return self._current_time

    def advance(
        self,
        *,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> None:
        """Advance time by the specified delta.

        Args:
            days: Number of days to advance.
            hours: Number of hours to advance.
            minutes: Number of minutes to advance.
            seconds: Number of seconds to advance.
            microseconds: Number of microseconds to advance.
        """
        delta = timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )
        self._current_time = self._current_time + delta

    def set_time(self, dt: datetime) -> None:
        """Set the clock to an absolute time.

        Args:
            dt: The datetime to set.
        """
        self._current_time = dt

    def reset(self) -> None:
        """Reset the clock to its initial time."""
        self._current_time = self._initial_time
