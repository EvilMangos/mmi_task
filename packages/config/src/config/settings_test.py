"""Tests for Settings and load_settings."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from config.settings import Settings, load_settings


def make_valid_env() -> dict[str, str]:
    """Create a minimal valid environment variable set."""
    return {
        "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF",
        "TELEGRAM_CHAT_ID": "-1001234567890",
        "SYMBOLS": "BTCUSDT,DOTUSDT,SOLUSDT",
        "IMBALANCE_THRESHOLD": "0.35",
    }


class TestSettings:
    """Tests for Settings class."""

    def test_loads_required_settings(self) -> None:
        """Settings loads all required environment variables."""
        env = make_valid_env()
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.telegram is not None
        assert settings.telegram.bot_token == "123456:ABC-DEF"
        assert settings.telegram.chat_id == "-1001234567890"

    def test_loads_binance_settings(self) -> None:
        """Settings correctly parses and stores Binance settings."""
        env = make_valid_env()
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.binance is not None
        assert settings.binance.symbols == ["BTCUSDT", "DOTUSDT", "SOLUSDT"]
        assert settings.binance.ws_url == "wss://stream.binance.com:9443/ws"
        assert settings.binance.top_n_levels == 10

    def test_loads_alerting_settings(self) -> None:
        """Settings correctly parses and stores alerting settings."""
        env = make_valid_env()
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.alerting is not None
        assert settings.alerting.imbalance_threshold == 0.35
        assert settings.alerting.cooldown_seconds == 30

    def test_loads_logging_settings(self) -> None:
        """Settings correctly parses and stores logging settings."""
        env = make_valid_env()
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.logging is not None
        assert settings.logging.log_level == "INFO"
        assert settings.logging.health_port is None

    def test_custom_optional_values(self) -> None:
        """Settings accepts custom values for optional parameters."""
        env = make_valid_env()
        env.update(
            {
                "TOP_N_LEVELS": "20",
                "ALERT_COOLDOWN_SECONDS": "60",
                "BINANCE_WS_URL": "wss://custom.binance.com/ws",
                "LOG_LEVEL": "DEBUG",
                "HEALTH_PORT": "8080",
            }
        )
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.binance is not None
        assert settings.binance.top_n_levels == 20
        assert settings.binance.ws_url == "wss://custom.binance.com/ws"

        assert settings.alerting is not None
        assert settings.alerting.cooldown_seconds == 60

        assert settings.logging is not None
        assert settings.logging.log_level == "DEBUG"
        assert settings.logging.health_port == 8080

    def test_missing_required_telegram_token_raises_error(self) -> None:
        """Missing TELEGRAM_BOT_TOKEN raises ValidationError."""
        env = make_valid_env()
        del env["TELEGRAM_BOT_TOKEN"]
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "telegram_bot_token" in str(exc_info.value).lower()

    def test_missing_required_chat_id_raises_error(self) -> None:
        """Missing TELEGRAM_CHAT_ID raises ValidationError."""
        env = make_valid_env()
        del env["TELEGRAM_CHAT_ID"]
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "telegram_chat_id" in str(exc_info.value).lower()

    def test_missing_required_symbols_raises_error(self) -> None:
        """Missing SYMBOLS raises ValidationError."""
        env = make_valid_env()
        del env["SYMBOLS"]
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "symbols" in str(exc_info.value).lower()

    def test_missing_required_threshold_raises_error(self) -> None:
        """Missing IMBALANCE_THRESHOLD raises ValidationError."""
        env = make_valid_env()
        del env["IMBALANCE_THRESHOLD"]
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "imbalance_threshold" in str(exc_info.value).lower()

    def test_invalid_threshold_value_raises_error(self) -> None:
        """Invalid IMBALANCE_THRESHOLD value raises ValidationError."""
        env = make_valid_env()
        env["IMBALANCE_THRESHOLD"] = "1.5"  # Out of range
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "imbalance_threshold" in str(exc_info.value).lower()

    def test_invalid_top_n_levels_raises_error(self) -> None:
        """Invalid TOP_N_LEVELS value raises ValidationError."""
        env = make_valid_env()
        env["TOP_N_LEVELS"] = "0"  # Below minimum
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "top_n_levels" in str(exc_info.value).lower()

    def test_invalid_ws_url_raises_error(self) -> None:
        """Invalid BINANCE_WS_URL raises ValidationError."""
        env = make_valid_env()
        env["BINANCE_WS_URL"] = "https://binance.com"
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "ws_url" in str(exc_info.value).lower()

    def test_negative_cooldown_raises_error(self) -> None:
        """Negative ALERT_COOLDOWN_SECONDS raises ValidationError."""
        env = make_valid_env()
        env["ALERT_COOLDOWN_SECONDS"] = "-10"
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
        assert "cooldown" in str(exc_info.value).lower()

    def test_negative_threshold_is_valid(self) -> None:
        """Negative IMBALANCE_THRESHOLD (for ask-heavy detection) is valid."""
        env = make_valid_env()
        env["IMBALANCE_THRESHOLD"] = "-0.35"
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.alerting is not None
        assert settings.alerting.imbalance_threshold == -0.35

    def test_symbols_normalized_to_uppercase(self) -> None:
        """SYMBOLS are normalized to uppercase."""
        env = make_valid_env()
        env["SYMBOLS"] = "btcusdt,dotusdt"
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.binance is not None
        assert settings.binance.symbols == ["BTCUSDT", "DOTUSDT"]

    def test_single_symbol_is_valid(self) -> None:
        """Single symbol (no comma) is valid."""
        env = make_valid_env()
        env["SYMBOLS"] = "BTCUSDT"
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        assert settings.binance is not None
        assert settings.binance.symbols == ["BTCUSDT"]

    def test_extra_env_vars_are_ignored(self) -> None:
        """Unknown environment variables are ignored."""
        env = make_valid_env()
        env["UNKNOWN_VAR"] = "should_be_ignored"
        env["ANOTHER_UNKNOWN"] = "also_ignored"
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()  # Should not raise

        assert settings.telegram is not None
        assert settings.binance is not None


class TestLoadSettings:
    """Tests for load_settings factory function."""

    def test_returns_settings_instance(self) -> None:
        """load_settings returns a Settings instance."""
        env = make_valid_env()
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()

        assert isinstance(settings, Settings)

    def test_each_call_creates_new_instance(self) -> None:
        """load_settings creates a new instance each time (no caching)."""
        env = make_valid_env()
        with patch.dict(os.environ, env, clear=True):
            settings1 = load_settings()
            settings2 = load_settings()

        assert settings1 is not settings2

    def test_propagates_validation_errors(self) -> None:
        """load_settings propagates validation errors from Settings."""
        env = make_valid_env()
        del env["TELEGRAM_BOT_TOKEN"]
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                load_settings()
