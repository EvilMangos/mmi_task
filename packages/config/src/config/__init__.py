"""Typed configuration settings for crypto orderbook alerts.

This package provides validated configuration management using Pydantic v2.
Settings are loaded from environment variables with sensible defaults.

Usage:
    from config import load_settings, Settings

    settings = load_settings()
    print(settings.telegram.bot_token)
    print(settings.binance.symbols)
    print(settings.alerting.imbalance_threshold)
"""

from config.alerting import AlertingSettings
from config.binance import BinanceSettings
from config.exceptions import ConfigurationError
from config.logging_config import LoggingSettings, LogLevel
from config.settings import Settings, load_settings
from config.telegram import TelegramSettings

__all__ = [
    # Main entry points
    "Settings",
    "load_settings",
    # Sub-settings models
    "TelegramSettings",
    "BinanceSettings",
    "AlertingSettings",
    "LoggingSettings",
    # Types
    "LogLevel",
    # Exceptions
    "ConfigurationError",
]
