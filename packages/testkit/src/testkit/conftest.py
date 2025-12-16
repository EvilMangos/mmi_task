"""Shared pytest fixtures and constants for use across the monorepo.

These fixtures are automatically available to any test that imports from testkit
or uses testkit as a dependency. See CLAUDE.md for usage examples.
"""

from datetime import datetime

import pytest

from testkit.binance_events import BinanceEvents
from testkit.fake_clock import FakeClock
from testkit.fake_notifier import FakeNotifier

# Shared test constants
DEFAULT_TEST_DATETIME = datetime(2025, 1, 1, 12, 0, 0)
DEFAULT_SYMBOL = "BTCUSDT"


@pytest.fixture
def fake_clock() -> FakeClock:
    """Create a FakeClock initialized to the default test datetime."""
    return FakeClock(initial_time=DEFAULT_TEST_DATETIME)


@pytest.fixture
def fake_notifier() -> FakeNotifier:
    """Create a fresh FakeNotifier instance."""
    return FakeNotifier()


@pytest.fixture
def binance_events() -> BinanceEvents:
    """Create a fresh BinanceEvents instance."""
    return BinanceEvents()
