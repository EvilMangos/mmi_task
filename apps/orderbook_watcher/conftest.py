"""Shared pytest fixtures for orderbook_watcher tests.

This module provides common test fixtures used across the orderbook_watcher
application tests.
"""

from datetime import datetime, timezone

import pytest
from orderbook_watcher.testing import FakeAlertNotifier
from testkit import FakeClock


@pytest.fixture
def fake_clock() -> FakeClock:
    """Create a FakeClock starting at a fixed time.

    The clock starts at 2025-01-15 12:00:00 UTC.
    """
    return FakeClock(datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def fake_notifier() -> FakeAlertNotifier:
    """Create a FakeAlertNotifier for testing."""
    return FakeAlertNotifier()
