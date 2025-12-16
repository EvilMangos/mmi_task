"""Pytest fixtures for domain_orderbook tests."""

from decimal import Decimal
from typing import Callable

import pytest

from domain_orderbook.level import OrderBookLevel


@pytest.fixture
def make_level() -> Callable[[str, str], OrderBookLevel]:
    """Factory fixture to create OrderBookLevel from string values."""

    def _make_level(price: str, qty: str) -> OrderBookLevel:
        return OrderBookLevel(price=Decimal(price), qty=Decimal(qty))

    return _make_level


@pytest.fixture
def sample_level(make_level: Callable[[str, str], OrderBookLevel]) -> OrderBookLevel:
    """A typical valid level for testing."""
    return make_level("100", "10")


@pytest.fixture
def sample_bids(
    make_level: Callable[[str, str], OrderBookLevel],
) -> tuple[OrderBookLevel, ...]:
    """Three bid levels at decreasing prices."""
    return (
        make_level("101", "30"),
        make_level("100", "20"),
        make_level("99", "10"),
    )


@pytest.fixture
def sample_asks(
    make_level: Callable[[str, str], OrderBookLevel],
) -> tuple[OrderBookLevel, ...]:
    """Three ask levels at increasing prices."""
    return (
        make_level("102", "10"),
        make_level("103", "20"),
        make_level("104", "30"),
    )
