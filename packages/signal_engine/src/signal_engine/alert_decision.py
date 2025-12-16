"""AlertDecision dataclass representing the result of signal evaluation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AlertDecision:
    """Result of evaluating whether an alert should be triggered.

    Attributes:
        should_alert: Whether an alert should be sent.
        reason: Human-readable explanation of the decision.
        ratio: The imbalance ratio that was evaluated.
        symbol: The trading symbol (e.g., "BTCUSDT").
    """

    should_alert: bool
    reason: str
    ratio: float
    symbol: str
