"""Tests for Settings and load_settings."""

import pytest

# patched_env is a context manager from conftest.py that sets up
# a clean environment with valid default values
from conftest import patched_env
from pydantic import ValidationError

from config.settings import Settings


class TestSettingsValidation:
    """Tests for Settings validation behavior."""

    def test_loads_with_valid_env(self) -> None:
        """Settings loads successfully with valid environment variables."""
        with patched_env():
            Settings(_env_file=None)  # Should not raise

    @pytest.mark.parametrize(
        ("remove_var", "expected_field"),
        [
            pytest.param(
                "TELEGRAM_BOT_TOKEN", "telegram_bot_token", id="missing_bot_token"
            ),
            pytest.param("TELEGRAM_CHAT_ID", "telegram_chat_id", id="missing_chat_id"),
            pytest.param("SYMBOLS", "symbols", id="missing_symbols"),
            pytest.param(
                "IMBALANCE_THRESHOLD", "imbalance_threshold", id="missing_threshold"
            ),
        ],
    )
    def test_missing_required_var_raises_error(
        self, remove_var: str, expected_field: str
    ) -> None:
        """Missing required environment variable raises ValidationError."""
        with patched_env(remove=[remove_var]):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)
            assert expected_field in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        ("override", "expected_message"),
        [
            pytest.param(
                {"IMBALANCE_THRESHOLD": "1.5"},
                "imbalance_threshold",
                id="threshold_above_one",
            ),
            pytest.param(
                {"TOP_N_LEVELS": "0"},
                "top_n_levels",
                id="top_n_below_minimum",
            ),
            pytest.param(
                {"BINANCE_WS_URL": "https://binance.com"},
                "ws_url",
                id="invalid_ws_protocol",
            ),
            pytest.param(
                {"ALERT_COOLDOWN_SECONDS": "-10"},
                "cooldown",
                id="negative_cooldown",
            ),
        ],
    )
    def test_invalid_value_raises_error(
        self, override: dict[str, str], expected_message: str
    ) -> None:
        """Invalid values for settings raise ValidationError."""
        with patched_env(overrides=override):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)
            assert expected_message in str(exc_info.value).lower()


class TestSettingsNormalization:
    """Tests for Settings normalization behavior."""

    def test_symbols_normalized_to_uppercase(self) -> None:
        """Symbols are normalized to uppercase regardless of input case."""
        with patched_env(overrides={"SYMBOLS": "btcusdt,dotusdt"}):
            settings = Settings(_env_file=None)
            assert settings.binance.symbols == ["BTCUSDT", "DOTUSDT"]

    def test_single_symbol_parsed_as_list(self) -> None:
        """Single symbol (no comma) is parsed as a list."""
        with patched_env(overrides={"SYMBOLS": "BTCUSDT"}):
            settings = Settings(_env_file=None)
            assert settings.binance.symbols == ["BTCUSDT"]

    def test_negative_threshold_accepted(self) -> None:
        """Negative threshold (for ask-heavy detection) is accepted."""
        with patched_env(overrides={"IMBALANCE_THRESHOLD": "-0.35"}):
            settings = Settings(_env_file=None)
            assert settings.alerting.imbalance_threshold == -0.35


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_optional_values_use_defaults(self) -> None:
        """Optional settings use default values when not specified."""
        with patched_env():
            settings = Settings(_env_file=None)
            # Verify defaults are applied (values from the implementation)
            assert settings.binance.top_n_levels == 10
            assert settings.alerting.cooldown_seconds == 30
            assert settings.logging.log_level == "INFO"
            assert settings.logging.health_port is None

    def test_custom_optional_values_override_defaults(self) -> None:
        """Custom values override defaults."""
        overrides = {
            "TOP_N_LEVELS": "20",
            "ALERT_COOLDOWN_SECONDS": "60",
            "LOG_LEVEL": "DEBUG",
            "HEALTH_PORT": "8080",
        }
        with patched_env(overrides=overrides):
            settings = Settings(_env_file=None)
            assert settings.binance.top_n_levels == 20
            assert settings.alerting.cooldown_seconds == 60
            assert settings.logging.log_level == "DEBUG"
            assert settings.logging.health_port == 8080


class TestSettingsExtras:
    """Tests for Settings behavior with unknown inputs."""

    def test_extra_env_vars_are_ignored(self) -> None:
        """Unknown environment variables are silently ignored."""
        overrides = {
            "UNKNOWN_VAR": "should_be_ignored",
            "ANOTHER_UNKNOWN": "also_ignored",
        }
        with patched_env(overrides=overrides):
            Settings(_env_file=None)  # Should not raise


class TestLoadSettings:
    """Tests for load_settings factory function."""

    def test_each_call_creates_new_instance(self) -> None:
        """Settings() creates a new instance each time (no caching)."""
        with patched_env():
            settings1 = Settings(_env_file=None)
            settings2 = Settings(_env_file=None)
            assert settings1 is not settings2
