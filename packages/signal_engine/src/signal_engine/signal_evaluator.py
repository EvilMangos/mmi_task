"""SignalEvaluator class for determining when to trigger alerts."""

from signal_engine.alert_decision import AlertDecision
from signal_engine.clock import Clock
from signal_engine.engine_config import EngineConfig
from signal_engine.symbol_state import SymbolState


class SignalEvaluator:
    """Evaluates imbalance ratios and decides whether to trigger alerts.

    Implements threshold checking, cooldown enforcement, and optional hysteresis
    logic on a per-symbol basis.
    """

    def __init__(self, config: EngineConfig, clock: Clock) -> None:
        """Initialize the evaluator with the given configuration.

        Args:
            config: Configuration specifying threshold, cooldown, and hysteresis settings.
            clock: Time source for cooldown calculations.
        """
        self._config = config
        self._clock = clock
        self._states: dict[str, SymbolState] = {}

    def evaluate(self, symbol: str, ratio: float) -> AlertDecision:
        """Evaluate whether an alert should be triggered for the given symbol and ratio.

        Args:
            symbol: The trading symbol (e.g., "BTCUSDT").
            ratio: The computed imbalance ratio.

        Returns:
            AlertDecision indicating whether to alert and why.
        """
        # Step 1: Get current time and symbol state
        now = self._clock.now()
        if symbol not in self._states:
            self._states[symbol] = SymbolState(is_armed=True, last_alert_time=None)

        state = self._states[symbol]

        # Step 2: Check if ratio is at or below threshold
        if ratio <= self._config.threshold:
            # Check hysteresis re-arm condition
            # Use small epsilon to handle floating-point precision issues
            # (e.g., 0.35 - 0.10 = 0.24999... due to IEEE 754)
            if self._config.hysteresis_enabled:
                epsilon = 1e-9
                rearm_threshold = self._config.threshold - self._config.hysteresis_delta
                if ratio <= rearm_threshold + epsilon:
                    state.is_armed = True
            return AlertDecision(
                should_alert=False,
                reason="Below threshold",
                ratio=ratio,
                symbol=symbol,
            )

        # Step 3: ratio > threshold at this point

        # Step 4: Check hysteresis armed state
        if self._config.hysteresis_enabled and not state.is_armed:
            return AlertDecision(
                should_alert=False,
                reason="Hysteresis: not re-armed",
                ratio=ratio,
                symbol=symbol,
            )

        # Step 5: Check cooldown
        if state.last_alert_time is not None:
            elapsed = (now - state.last_alert_time).total_seconds()
            if elapsed < self._config.cooldown_seconds:
                return AlertDecision(
                    should_alert=False,
                    reason="Cooldown active",
                    ratio=ratio,
                    symbol=symbol,
                )

        # Step 6: All checks passed - trigger alert
        state.last_alert_time = now
        if self._config.hysteresis_enabled:
            state.is_armed = False

        return AlertDecision(
            should_alert=True,
            reason="Threshold exceeded",
            ratio=ratio,
            symbol=symbol,
        )
