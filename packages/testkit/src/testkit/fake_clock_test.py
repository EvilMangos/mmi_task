"""Tests for FakeClock - a deterministic time source for testing."""

from datetime import datetime, timedelta

from testkit.fake_clock import FakeClock


class TestFakeClockInitialization:
    """Test FakeClock initialization and basic state."""

    def test_creates_with_initial_time(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)
        assert clock.now() == initial

    def test_creates_with_default_epoch_time(self):
        clock = FakeClock()
        # Should default to epoch or a reasonable default
        assert clock.now() is not None
        assert isinstance(clock.now(), datetime)

    def test_now_returns_datetime(self):
        clock = FakeClock(initial_time=datetime(2025, 1, 1, 12, 0, 0))
        result = clock.now()
        assert isinstance(result, datetime)


class TestFakeClockAdvance:
    """Test time advancement functionality."""

    def test_advance_by_seconds(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(seconds=30)

        expected = initial + timedelta(seconds=30)
        assert clock.now() == expected

    def test_advance_by_minutes(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(minutes=5)

        expected = initial + timedelta(minutes=5)
        assert clock.now() == expected

    def test_advance_by_hours(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(hours=2)

        expected = initial + timedelta(hours=2)
        assert clock.now() == expected

    def test_advance_by_multiple_units(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(hours=2, minutes=30, seconds=45)

        expected = initial + timedelta(hours=2, minutes=30, seconds=45)
        assert clock.now() == expected

    def test_advance_by_days(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(days=7)

        expected = initial + timedelta(days=7)
        assert clock.now() == expected

    def test_advance_with_no_arguments_does_nothing(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance()

        assert clock.now() == initial

    def test_advance_multiple_times_accumulates(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(seconds=10)
        clock.advance(seconds=20)
        clock.advance(minutes=1)

        expected = (
            initial
            + timedelta(seconds=10)
            + timedelta(seconds=20)
            + timedelta(minutes=1)
        )
        assert clock.now() == expected

    def test_advance_by_negative_values_goes_backward(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(seconds=-30)

        expected = initial + timedelta(seconds=-30)
        assert clock.now() == expected


class TestFakeClockSetTime:
    """Test absolute time setting."""

    def test_set_time_changes_current_time(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        new_time = datetime(2025, 6, 15, 18, 30, 45)
        clock.set_time(new_time)

        assert clock.now() == new_time

    def test_set_time_can_go_backward(self):
        initial = datetime(2025, 6, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        earlier_time = datetime(2025, 1, 1, 12, 0, 0)
        clock.set_time(earlier_time)

        assert clock.now() == earlier_time

    def test_set_time_then_advance_works(self):
        clock = FakeClock(initial_time=datetime(2025, 1, 1, 12, 0, 0))

        new_time = datetime(2025, 3, 15, 10, 0, 0)
        clock.set_time(new_time)
        clock.advance(hours=1)

        expected = new_time + timedelta(hours=1)
        assert clock.now() == expected


class TestFakeClockReset:
    """Test reset functionality."""

    def test_reset_returns_to_initial_time(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(hours=5)
        clock.reset()

        assert clock.now() == initial

    def test_reset_after_set_time_returns_to_initial(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.set_time(datetime(2025, 6, 1, 12, 0, 0))
        clock.reset()

        assert clock.now() == initial

    def test_reset_multiple_times_is_idempotent(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(hours=1)
        clock.reset()
        clock.reset()
        clock.reset()

        assert clock.now() == initial


class TestFakeClockEdgeCases:
    """Test edge cases and error conditions."""

    def test_microseconds_precision(self):
        initial = datetime(2025, 1, 1, 12, 0, 0, 123456)
        clock = FakeClock(initial_time=initial)

        assert clock.now() == initial
        assert clock.now().microsecond == 123456

    def test_advance_by_microseconds(self):
        initial = datetime(2025, 1, 1, 12, 0, 0)
        clock = FakeClock(initial_time=initial)

        clock.advance(microseconds=500000)

        expected = initial + timedelta(microseconds=500000)
        assert clock.now() == expected

    def test_leap_year_handling(self):
        initial = datetime(2024, 2, 28, 23, 59, 59)
        clock = FakeClock(initial_time=initial)

        clock.advance(seconds=2)

        expected = datetime(2024, 2, 29, 0, 0, 1)
        assert clock.now() == expected

    def test_year_boundary_crossing(self):
        initial = datetime(2024, 12, 31, 23, 59, 59)
        clock = FakeClock(initial_time=initial)

        clock.advance(seconds=2)

        expected = datetime(2025, 1, 1, 0, 0, 1)
        assert clock.now() == expected

    def test_timezone_aware_datetime(self):
        from datetime import timezone

        initial = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        clock = FakeClock(initial_time=initial)

        assert clock.now() == initial
        assert clock.now().tzinfo == timezone.utc


class TestFakeClockProtocolCompliance:
    """Test that FakeClock implements Clock protocol correctly."""

    def test_has_now_method(self):
        clock = FakeClock()
        assert hasattr(clock, "now")
        assert callable(clock.now)

    def test_now_signature_matches_protocol(self):
        clock = FakeClock()
        # Should be callable with no arguments
        result = clock.now()
        assert isinstance(result, datetime)
