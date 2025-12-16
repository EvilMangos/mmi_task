"""Binance connector settings."""

from pydantic import BaseModel, field_validator

DEFAULT_BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
DEFAULT_TOP_N_LEVELS = 10

MIN_TOP_N_LEVELS = 1
MAX_TOP_N_LEVELS = 100


class BinanceSettings(BaseModel, frozen=True):
    """Settings for Binance WebSocket connection.

    Attributes:
        symbols: List of trading pair symbols to watch (e.g., ["BTCUSDT", "SOLUSDT"]).
        ws_url: Binance WebSocket URL.
        top_n_levels: Number of order book levels to consider for imbalance.
    """

    symbols: list[str]
    ws_url: str = DEFAULT_BINANCE_WS_URL
    top_n_levels: int = DEFAULT_TOP_N_LEVELS

    @field_validator("symbols", mode="before")
    @classmethod
    def parse_symbols(cls, v: str | list[str]) -> list[str]:
        """Parse symbols from comma-separated string or list.

        Normalizes symbols to uppercase and strips whitespace.
        """
        if isinstance(v, str):
            symbols = [s.strip().upper() for s in v.split(",") if s.strip()]
        else:
            symbols = [s.strip().upper() for s in v if s.strip()]

        if not symbols:
            raise ValueError("symbols must contain at least one item")
        return symbols

    @field_validator("ws_url")
    @classmethod
    def validate_ws_url(cls, v: str) -> str:
        """Validate that ws_url starts with ws:// or wss://."""
        stripped = v.strip()
        if not stripped.startswith(("ws://", "wss://")):
            raise ValueError("ws_url must start with ws:// or wss://")
        return stripped

    @field_validator("top_n_levels")
    @classmethod
    def validate_top_n_levels(cls, v: int) -> int:
        """Validate that top_n_levels is within valid range."""
        if v < MIN_TOP_N_LEVELS or v > MAX_TOP_N_LEVELS:
            raise ValueError(
                f"top_n_levels must be between {MIN_TOP_N_LEVELS} and {MAX_TOP_N_LEVELS}"
            )
        return v
