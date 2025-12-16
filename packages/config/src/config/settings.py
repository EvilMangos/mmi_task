"""Main settings aggregator that loads configuration from environment variables."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.alerting import DEFAULT_COOLDOWN_SECONDS, AlertingSettings
from config.binance import DEFAULT_BINANCE_WS_URL, DEFAULT_TOP_N_LEVELS, BinanceSettings
from config.logging_config import DEFAULT_LOG_LEVEL, LoggingSettings, LogLevel
from config.telegram import TelegramSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment Variables:
        TELEGRAM_BOT_TOKEN: Telegram bot API token (required).
        TELEGRAM_CHAT_ID: Target chat/channel ID (required).
        SYMBOLS: Comma-separated trading pairs (required, e.g., "BTCUSDT,DOTUSDT").
        IMBALANCE_THRESHOLD: Alert threshold (required, e.g., "0.35").
        TOP_N_LEVELS: Order book depth (optional, default 10).
        ALERT_COOLDOWN_SECONDS: Alert cooldown period (optional, default 30).
        BINANCE_WS_URL: WebSocket URL override (optional).
        LOG_LEVEL: Logging level (optional, default INFO).
        HEALTH_PORT: Health endpoint port (optional, disabled by default).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Raw environment variable mappings
    telegram_bot_token: str
    telegram_chat_id: str
    symbols: str
    imbalance_threshold: float
    top_n_levels: int = DEFAULT_TOP_N_LEVELS
    alert_cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    binance_ws_url: str = DEFAULT_BINANCE_WS_URL
    log_level: LogLevel = DEFAULT_LOG_LEVEL
    health_port: int | None = None

    # Composed settings objects
    telegram: TelegramSettings | None = None
    binance: BinanceSettings | None = None
    alerting: AlertingSettings | None = None
    logging: LoggingSettings | None = None

    @model_validator(mode="after")
    def build_sub_settings(self) -> "Settings":
        """Build sub-settings objects from flat environment variables."""
        object.__setattr__(
            self,
            "telegram",
            TelegramSettings(
                bot_token=self.telegram_bot_token,
                chat_id=self.telegram_chat_id,
            ),
        )
        object.__setattr__(
            self,
            "binance",
            BinanceSettings(
                symbols=self.symbols,
                ws_url=self.binance_ws_url,
                top_n_levels=self.top_n_levels,
            ),
        )
        object.__setattr__(
            self,
            "alerting",
            AlertingSettings(
                imbalance_threshold=self.imbalance_threshold,
                cooldown_seconds=self.alert_cooldown_seconds,
            ),
        )
        object.__setattr__(
            self,
            "logging",
            LoggingSettings(
                log_level=self.log_level,
                health_port=self.health_port,
            ),
        )
        return self


def load_settings() -> Settings:
    """Load settings from environment variables.

    Returns:
        Settings object with all configuration loaded and validated.

    Raises:
        pydantic.ValidationError: If required variables are missing or invalid.
    """
    return Settings()
