"""Alerting and signal engine settings."""

from pydantic import BaseModel, field_validator

DEFAULT_COOLDOWN_SECONDS = 30


class AlertingSettings(BaseModel, frozen=True):
    """Settings for alert threshold and cooldown behavior.

    Attributes:
        imbalance_threshold: Threshold for imbalance ratio to trigger alerts.
            Must be in range (-1.0, 1.0). Positive values detect bid-heavy
            imbalance, negative values detect ask-heavy imbalance.
        cooldown_seconds: Minimum seconds between alerts for the same symbol.
    """

    imbalance_threshold: float
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS

    @field_validator("imbalance_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate that threshold is within valid range (-1.0, 1.0)."""
        if v <= -1.0 or v >= 1.0:
            raise ValueError("imbalance_threshold must be in range (-1.0, 1.0)")
        return v

    @field_validator("cooldown_seconds")
    @classmethod
    def validate_cooldown(cls, v: int) -> int:
        """Validate that cooldown_seconds is non-negative."""
        if v < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        return v
