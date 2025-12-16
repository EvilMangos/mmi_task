"""OrderBookLevel dataclass representing a single price/quantity level."""

from dataclasses import dataclass
from decimal import Decimal


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
        # Check for NaN/Inf in price
        if not self.price.is_finite():
            raise ValueError("price must be finite (not NaN or Inf)")

        # Check for NaN/Inf in qty
        if not self.qty.is_finite():
            raise ValueError("qty must be finite (not NaN or Inf)")

        # Check for negative price
        if self.price < 0:
            raise ValueError("price must be non-negative")

        # Check for negative qty
        if self.qty < 0:
            raise ValueError("qty must be non-negative")
