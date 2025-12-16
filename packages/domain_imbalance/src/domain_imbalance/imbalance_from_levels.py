"""Helper function to compute imbalance from order book levels."""

from collections.abc import Sequence

from domain_imbalance.imbalance_ratio import imbalance_ratio


def imbalance_from_levels(
    bids: Sequence[tuple[float, float]],
    asks: Sequence[tuple[float, float]],
) -> float:
    """Compute imbalance ratio from order book levels.

    Each level is a tuple of (price, volume). This function sums the volumes
    from all bid and ask levels, then delegates to imbalance_ratio.

    Args:
        bids: Sequence of (price, volume) tuples for bid side.
        asks: Sequence of (price, volume) tuples for ask side.

    Returns:
        Imbalance ratio in the range [-1.0, 1.0].
    """
    bid_volume = sum(volume for _, volume in bids)
    ask_volume = sum(volume for _, volume in asks)
    return imbalance_ratio(bid_volume, ask_volume)
