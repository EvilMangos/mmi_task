"""Test support: AlertPayload factory for test data."""

from notifier_telegram.alert_payload import AlertPayload


def make_payload(
    symbol: str = "BTCUSDT",
    ratio: float = 0.45,
    bid_volume: float = 150000.0,
    ask_volume: float = 85000.0,
    timestamp: float = 1702800000.0,
    threshold: float = 0.35,
) -> AlertPayload:
    """Create an AlertPayload with sensible defaults for testing."""
    return AlertPayload(
        symbol=symbol,
        ratio=ratio,
        bid_volume=bid_volume,
        ask_volume=ask_volume,
        timestamp=timestamp,
        threshold=threshold,
    )
