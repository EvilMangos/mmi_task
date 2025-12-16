"""Watcher class for processing order book snapshots.

The Watcher is the core processing component that:
1. Extracts top N levels from order book snapshots
2. Computes imbalance ratios
3. Evaluates against threshold with cooldown
4. Sends alerts via the notifier
"""

from contracts import (
    Notifier,
    PermanentNotifierError,
    TransientNotifierError,
)
from domain_imbalance import imbalance_ratio
from domain_orderbook import OrderBookSnapshot, sum_volume, top_n_asks, top_n_bids
from notifier_telegram import AlertPayload
from observability import get_logger
from signal_engine import SignalEvaluator

logger = get_logger(__name__)


class Watcher:
    """Processes order book snapshots and triggers alerts.

    Coordinates between domain functions, signal evaluation, and notification.
    """

    def __init__(
        self,
        evaluator: SignalEvaluator,
        notifier: Notifier,
        threshold: float,
        top_n_levels: int,
    ) -> None:
        """Initialize the watcher with dependencies.

        Args:
            evaluator: SignalEvaluator for threshold and cooldown decisions.
            notifier: Notifier implementation with send_alert method.
            threshold: The imbalance threshold value.
            top_n_levels: Number of order book levels to consider.
        """
        self._evaluator = evaluator
        self._notifier = notifier
        self._threshold = threshold
        self._top_n_levels = top_n_levels

    async def process_snapshot(self, snapshot: OrderBookSnapshot) -> None:
        """Process an order book snapshot and potentially send an alert.

        Args:
            snapshot: The order book snapshot to process.
        """
        # Step 1: Extract top N levels
        top_bids = top_n_bids(snapshot.bids, self._top_n_levels)
        top_asks = top_n_asks(snapshot.asks, self._top_n_levels)

        # Step 2: Sum volumes (Decimal -> float)
        bid_volume = float(sum_volume(top_bids))
        ask_volume = float(sum_volume(top_asks))

        # Step 3: Compute imbalance ratio
        ratio = imbalance_ratio(bid_volume, ask_volume)

        # Step 4: Evaluate signal (evaluator manages its own time via injected clock)
        decision = self._evaluator.evaluate(snapshot.symbol, ratio)

        # Step 6: Send alert if triggered
        if decision.should_alert:
            alert = AlertPayload(
                symbol=snapshot.symbol,
                ratio=ratio,
                bid_volume=bid_volume,
                ask_volume=ask_volume,
                timestamp=snapshot.timestamp,
                threshold=self._threshold,
            )

            try:
                await self._notifier.send_alert(alert)
            except TransientNotifierError as e:
                logger.warning(
                    "Transient notifier error for %s: %s",
                    snapshot.symbol,
                    str(e),
                )
            except PermanentNotifierError as e:
                logger.error(
                    "Permanent notifier error for %s: %s",
                    snapshot.symbol,
                    str(e),
                )
