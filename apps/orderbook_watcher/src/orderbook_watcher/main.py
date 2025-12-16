"""Main entry point for orderbook-watcher service."""

import asyncio
import signal
import sys

from config import load_settings
from connector_binance import BinanceFeed
from notifier_telegram import TelegramNotifier
from observability import get_logger
from signal_engine import EngineConfig, SignalEvaluator

from orderbook_watcher.real_clock import RealClock
from orderbook_watcher.watcher import Watcher

logger = get_logger(__name__)


def main() -> None:
    """Run the orderbook watcher service."""
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")


async def _async_main() -> None:
    """Async main function that runs the watcher loop."""
    # 1. Load settings (fails fast if invalid)
    try:
        settings = load_settings()
    except Exception as e:
        logger.error("Failed to load settings: %s", e)
        sys.exit(1)

    logger.info("Starting orderbook watcher for symbols: %s", settings.binance.symbols)

    # 2. Build EngineConfig from AlertingSettings
    engine_config = EngineConfig(
        threshold=settings.alerting.imbalance_threshold,
        cooldown_seconds=float(settings.alerting.cooldown_seconds),
        hysteresis_enabled=False,  # Not configurable via env yet
    )

    # 3. Create components (clock is injected into evaluator per DIP)
    clock = RealClock()
    evaluator = SignalEvaluator(engine_config, clock)

    # 4. Setup shutdown event
    shutdown_event = asyncio.Event()

    def handle_shutdown(sig: signal.Signals) -> None:
        logger.info("Received signal %s, initiating shutdown", sig.name)
        shutdown_event.set()

    # Register signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, sig)

    # 5. Run with context managers for cleanup
    async with TelegramNotifier(
        bot_token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
    ) as notifier:
        async with BinanceFeed(settings.binance) as feed:
            watcher = Watcher(
                evaluator=evaluator,
                notifier=notifier,
                threshold=settings.alerting.imbalance_threshold,
                top_n_levels=settings.binance.top_n_levels,
            )

            logger.info("Connected to Binance, processing snapshots...")

            # 6. Process snapshots until shutdown
            try:
                async for snapshot in feed.snapshots():
                    if shutdown_event.is_set():
                        break
                    await watcher.process_snapshot(snapshot)
            except Exception as e:
                logger.error("Error processing snapshots: %s", e)
                raise

    logger.info("Orderbook watcher shutdown complete")


if __name__ == "__main__":
    main()
