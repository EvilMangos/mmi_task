"""EngineConfig dataclass for signal evaluator configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConfig:
    """Configuration for the SignalEvaluator.

    Attributes:
        threshold: Alert when ratio > threshold.
        cooldown_seconds: Minimum seconds between alerts per symbol.
        hysteresis_enabled: Whether hysteresis logic is active.
        hysteresis_delta: Ratio must drop below (threshold - delta) to re-arm.
    """

    threshold: float
    cooldown_seconds: float
    hysteresis_enabled: bool = False
    hysteresis_delta: float = 0.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        if self.hysteresis_delta < 0:
            raise ValueError("hysteresis_delta must be >= 0")
