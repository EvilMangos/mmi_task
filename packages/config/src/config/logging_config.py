"""Logging and observability settings."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

DEFAULT_LOG_LEVEL: LogLevel = "INFO"

MIN_PORT = 1
MAX_PORT = 65535


class LoggingSettings(BaseModel):
    """Settings for logging and health check endpoint.

    Attributes:
        log_level: Logging level for the application.
        health_port: Optional port for health check endpoint. None means disabled.
    """

    model_config = ConfigDict(frozen=True)

    log_level: LogLevel = DEFAULT_LOG_LEVEL
    health_port: int | None = None

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        """Normalize log level to uppercase."""
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("health_port")
    @classmethod
    def validate_health_port(cls, v: int | None) -> int | None:
        """Validate that health_port is within valid range if set."""
        if v is not None and (v < MIN_PORT or v > MAX_PORT):
            raise ValueError(f"health_port must be between {MIN_PORT} and {MAX_PORT}")
        return v
