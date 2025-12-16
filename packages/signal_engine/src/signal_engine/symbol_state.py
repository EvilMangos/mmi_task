"""SymbolState dataclass for tracking per-symbol alert state."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SymbolState:
    """Internal state for tracking alerts per symbol.

    Attributes:
        is_armed: Whether the symbol is armed for alerting (used with hysteresis).
        last_alert_time: The timestamp of the last alert sent for this symbol.
    """

    is_armed: bool = True
    last_alert_time: datetime | None = None
