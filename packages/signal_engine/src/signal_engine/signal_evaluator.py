"""SignalEvaluator class for determining when to trigger alerts."""

from datetime import datetime

from signal_engine.alert_decision import AlertDecision
from contracts import Clock
from signal_engine.engine_config import EngineConfig
from signal_engine.symbol_state import SymbolState

_FLOAT_EPSILON = 1e-9


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

    def _no_alert(self, symbol: str, ratio: float, reason: str) -> AlertDecision:
        """Create an AlertDecision indicating no alert should be triggered."""
        return AlertDecision(
            should_alert=False,
            reason=reason,
            ratio=ratio,
            symbol=symbol,
        )

    def _alert(self, symbol: str, ratio: float) -> AlertDecision:
        """Create an AlertDecision indicating an alert should be triggered."""
        return AlertDecision(
            should_alert=True,
            reason="Threshold exceeded",
            ratio=ratio,
            symbol=symbol,
        )

    def _maybe_rearm(self, state: SymbolState, ratio: float) -> None:
        """Re-arm the hysteresis state if ratio has dropped below the re-arm threshold."""
        if not self._config.hysteresis_enabled:
            return
        rearm_threshold = self._config.threshold - self._config.hysteresis_delta
        if ratio <= rearm_threshold + _FLOAT_EPSILON:
            state.is_armed = True

    def _is_cooldown_active(self, state: SymbolState, now: datetime) -> bool:
        """Check if the cooldown period is still active for the given state."""
        if state.last_alert_time is None:
            return False
        elapsed = (now - state.last_alert_time).total_seconds()
        return elapsed < self._config.cooldown_seconds

    def evaluate(self, symbol: str, ratio: float) -> AlertDecision:
        """Evaluate whether an alert should be triggered for the given symbol and ratio.

        Args:
            symbol: The trading symbol (e.g., "BTCUSDT").
            ratio: The computed imbalance ratio.

        Returns:
            AlertDecision indicating whether to alert and why.
        """
        now = self._clock.now()
        if symbol not in self._states:
            self._states[symbol] = SymbolState(is_armed=True, last_alert_time=None)

        state = self._states[symbol]

        if ratio <= self._config.threshold:
            self._maybe_rearm(state, ratio)
            return self._no_alert(symbol, ratio, "Below threshold")

        if self._config.hysteresis_enabled and not state.is_armed:
            return self._no_alert(symbol, ratio, "Hysteresis: not re-armed")

        if self._is_cooldown_active(state, now):
            return self._no_alert(symbol, ratio, "Cooldown active")

        state.last_alert_time = now
        if self._config.hysteresis_enabled:
            state.is_armed = False

        return self._alert(symbol, ratio)
