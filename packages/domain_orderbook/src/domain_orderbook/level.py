"""OrderBookLevel dataclass representing a single price/quantity level."""

from dataclasses import dataclass
from decimal import Decimal


def _validate_non_negative_finite(value: Decimal, field_name: str) -> None:
    """Validate that a Decimal value is finite and non-negative.

    Args:
        value: The Decimal value to validate.
        field_name: Name of the field for error messages.

    Raises:
        ValueError: If value is not finite or is negative.
    """
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite (not NaN or Inf)")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True)
class OrderBookLevel:
    """A single order book level with price and quantity.

    Attributes:
        price: The price at this level (must be non-negative, finite).
        qty: The quantity at this level (must be non-negative, finite).
    """

    price: Decimal
    qty: Decimal

    def __post_init__(self) -> None:
        """Validate price and qty are non-negative and finite."""
        _validate_non_negative_finite(self.price, "price")
        _validate_non_negative_finite(self.qty, "qty")
