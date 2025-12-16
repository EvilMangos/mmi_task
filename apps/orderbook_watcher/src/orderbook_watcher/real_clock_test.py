"""Unit tests for the RealClock class.

RealClock is a production implementation of the Clock protocol
that returns actual system time in UTC.
"""

import time
from datetime import datetime, timezone

from orderbook_watcher.real_clock import RealClock


class TestRealClock:
    """Tests for RealClock."""

    def test_real_clock_returns_datetime(self) -> None:
        """RealClock.now() returns a datetime object."""
        clock = RealClock()

        result = clock.now()

        assert isinstance(result, datetime)

    def test_real_clock_returns_utc_timezone(self) -> None:
        """RealClock.now() returns a datetime with UTC timezone."""
        clock = RealClock()

        result = clock.now()

        # Should have timezone info set to UTC
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_real_clock_advances_over_time(self) -> None:
        """Second call to now() returns time >= first call."""
        clock = RealClock()

        first_time = clock.now()
        # Small sleep to ensure time advances
        time.sleep(0.001)  # 1 millisecond
        second_time = clock.now()

        assert second_time >= first_time

    def test_real_clock_time_is_reasonable(self) -> None:
        """RealClock returns a time that is reasonably close to actual time."""
        clock = RealClock()

        result = clock.now()
        expected = datetime.now(timezone.utc)

        # Should be within 1 second of actual time
        diff = abs((result - expected).total_seconds())
        assert diff < 1.0

    def test_real_clock_implements_clock_protocol(self) -> None:
        """RealClock can be used where Clock protocol is expected."""
        from testkit import Clock

        clock = RealClock()

        # Should satisfy the Clock protocol
        assert hasattr(clock, "now")
        assert callable(clock.now)

        # Should be usable as Clock type
        def use_clock(c: Clock) -> datetime:
            return c.now()

        result = use_clock(clock)
        assert isinstance(result, datetime)
