"""Tests for LoggingSettings."""

import pytest
from pydantic import ValidationError

from config.logging_config import DEFAULT_LOG_LEVEL, LoggingSettings


class TestLoggingSettings:
    """Tests for LoggingSettings validation."""

    def test_valid_settings_with_defaults(self) -> None:
        """Default values are applied correctly."""
        settings = LoggingSettings()
        assert settings.log_level == DEFAULT_LOG_LEVEL
        assert settings.health_port is None

    def test_all_valid_log_levels(self) -> None:
        """All valid log levels are accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = LoggingSettings(log_level=level)  # type: ignore[arg-type]
            assert settings.log_level == level

    def test_normalizes_log_level_to_uppercase(self) -> None:
        """Log level is normalized to uppercase."""
        settings = LoggingSettings(log_level="debug")  # type: ignore[arg-type]
        assert settings.log_level == "DEBUG"

    def test_normalizes_mixed_case_log_level(self) -> None:
        """Mixed case log level is normalized to uppercase."""
        settings = LoggingSettings(log_level="WaRnInG")  # type: ignore[arg-type]
        assert settings.log_level == "WARNING"

    def test_strips_whitespace_from_log_level(self) -> None:
        """Whitespace is stripped from log level."""
        settings = LoggingSettings(log_level="  info  ")  # type: ignore[arg-type]
        assert settings.log_level == "INFO"

    def test_invalid_log_level_raises_error(self) -> None:
        """Invalid log level raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(log_level="TRACE")  # type: ignore[arg-type]
        assert "log_level" in str(exc_info.value)

    def test_valid_health_port(self) -> None:
        """Valid health port is accepted."""
        settings = LoggingSettings(health_port=8080)
        assert settings.health_port == 8080

    def test_minimum_valid_port(self) -> None:
        """Minimum valid port (1) is accepted."""
        settings = LoggingSettings(health_port=1)
        assert settings.health_port == 1

    def test_maximum_valid_port(self) -> None:
        """Maximum valid port (65535) is accepted."""
        settings = LoggingSettings(health_port=65535)
        assert settings.health_port == 65535

    def test_port_zero_raises_error(self) -> None:
        """Port 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(health_port=0)
        assert "health_port must be between 1 and 65535" in str(exc_info.value)

    def test_negative_port_raises_error(self) -> None:
        """Negative port raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(health_port=-1)
        assert "health_port must be between 1 and 65535" in str(exc_info.value)

    def test_port_above_maximum_raises_error(self) -> None:
        """Port above 65535 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(health_port=65536)
        assert "health_port must be between 1 and 65535" in str(exc_info.value)

    def test_none_health_port_is_valid(self) -> None:
        """None health_port (disabled) is valid."""
        settings = LoggingSettings(health_port=None)
        assert settings.health_port is None

    def test_settings_are_immutable(self) -> None:
        """Settings object is frozen and cannot be modified."""
        settings = LoggingSettings()
        with pytest.raises(ValidationError):
            settings.log_level = "ERROR"  # type: ignore[misc]

    def test_common_service_ports(self) -> None:
        """Common service ports are valid."""
        for port in [80, 443, 3000, 5000, 8000, 8080, 9000]:
            settings = LoggingSettings(health_port=port)
            assert settings.health_port == port
