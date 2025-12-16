"""AlertPayload dataclass for imbalance alert data.

AlertPayload is a frozen dataclass containing all data needed to format and send
an imbalance alert via a notification channel.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AlertPayload:
    """Immutable container for imbalance alert data.

    Attributes:
        symbol: Trading pair symbol (e.g., "BTCUSDT").
        ratio: Computed imbalance ratio, range [-1.0, 1.0].
        bid_volume: Total bid volume for top N levels.
        ask_volume: Total ask volume for top N levels.
        timestamp: Unix timestamp (seconds since epoch).
        threshold: The threshold that was exceeded to trigger this alert.
    """

    symbol: str
    ratio: float
    bid_volume: float
    ask_volume: float
    timestamp: float
    threshold: float

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol must not be empty or whitespace")
        if self.timestamp < 0:
            raise ValueError("timestamp must not be negative")
