"""Core imbalance ratio calculation."""


def imbalance_ratio(bid_volume: float, ask_volume: float) -> float:
    """Calculate the imbalance ratio between bid and ask volumes.

    Formula: (bid_volume - ask_volume) / (bid_volume + ask_volume)

    Args:
        bid_volume: Total volume on the bid side (must be >= 0).
        ask_volume: Total volume on the ask side (must be >= 0).

    Returns:
        Imbalance ratio in the range [-1.0, 1.0].
        Returns 0.0 when both volumes are zero (avoids division by zero).
    """
    total = bid_volume + ask_volume
    if total == 0.0:
        return 0.0
    return (bid_volume - ask_volume) / total
