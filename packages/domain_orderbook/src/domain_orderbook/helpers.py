"""Helper functions for order book operations."""

from collections.abc import Iterable
from decimal import Decimal
from operator import attrgetter

from domain_orderbook.level import OrderBookLevel

_PRICE_KEY = attrgetter("price")


def _validate_n(n: int) -> None:
    """Validate that n is non-negative.

    Args:
        n: The value to validate.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")


def normalize_bids(levels: Iterable[OrderBookLevel]) -> tuple[OrderBookLevel, ...]:
    """Sort levels by price descending (highest first).

    Args:
        levels: Iterable of OrderBookLevel objects.

    Returns:
        Tuple of levels sorted by price descending.
    """
    return tuple(sorted(levels, key=_PRICE_KEY, reverse=True))


def normalize_asks(levels: Iterable[OrderBookLevel]) -> tuple[OrderBookLevel, ...]:
    """Sort levels by price ascending (lowest first).

    Args:
        levels: Iterable of OrderBookLevel objects.

    Returns:
        Tuple of levels sorted by price ascending.
    """
    return tuple(sorted(levels, key=_PRICE_KEY))


def top_n_bids(levels: Iterable[OrderBookLevel], n: int) -> tuple[OrderBookLevel, ...]:
    """Return N highest-priced levels, sorted descending.

    Args:
        levels: Iterable of OrderBookLevel objects.
        n: Number of top levels to return.

    Returns:
        Tuple of N highest-priced levels sorted by price descending.

    Raises:
        ValueError: If n is negative.
    """
    _validate_n(n)
    normalized = normalize_bids(levels)
    return normalized[:n]


def top_n_asks(levels: Iterable[OrderBookLevel], n: int) -> tuple[OrderBookLevel, ...]:
    """Return N lowest-priced levels, sorted ascending.

    Args:
        levels: Iterable of OrderBookLevel objects.
        n: Number of top levels to return.

    Returns:
        Tuple of N lowest-priced levels sorted by price ascending.

    Raises:
        ValueError: If n is negative.
    """
    _validate_n(n)
    normalized = normalize_asks(levels)
    return normalized[:n]


def sum_volume(levels: Iterable[OrderBookLevel]) -> Decimal:
    """Sum all quantities from the given levels.

    Args:
        levels: Iterable of OrderBookLevel objects.

    Returns:
        Sum of all quantities as Decimal. Returns Decimal("0") for empty input.
    """
    return sum((level.qty for level in levels), start=Decimal("0"))
