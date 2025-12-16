"""Tests for AlertingSettings."""

import pytest
from pydantic import ValidationError

from config.alerting import DEFAULT_COOLDOWN_SECONDS, AlertingSettings


class TestAlertingSettings:
    """Tests for AlertingSettings validation."""

    def test_valid_settings_with_defaults(self) -> None:
        """Valid threshold with default cooldown is accepted."""
        settings = AlertingSettings(imbalance_threshold=0.35)
        assert settings.imbalance_threshold == 0.35
        assert settings.cooldown_seconds == DEFAULT_COOLDOWN_SECONDS

    def test_valid_positive_threshold(self) -> None:
        """Positive threshold near boundary is accepted."""
        settings = AlertingSettings(imbalance_threshold=0.99)
        assert settings.imbalance_threshold == 0.99

    def test_valid_negative_threshold(self) -> None:
        """Negative threshold for ask-heavy detection is accepted."""
        settings = AlertingSettings(imbalance_threshold=-0.35)
        assert settings.imbalance_threshold == -0.35

    def test_valid_threshold_near_negative_boundary(self) -> None:
        """Negative threshold near boundary is accepted."""
        settings = AlertingSettings(imbalance_threshold=-0.99)
        assert settings.imbalance_threshold == -0.99

    def test_threshold_exactly_zero_is_valid(self) -> None:
        """Threshold of exactly zero is valid."""
        settings = AlertingSettings(imbalance_threshold=0.0)
        assert settings.imbalance_threshold == 0.0

    @pytest.mark.parametrize(
        "invalid_threshold",
        [
            pytest.param(1.0, id="exactly_positive_one"),
            pytest.param(-1.0, id="exactly_negative_one"),
            pytest.param(1.5, id="above_one"),
            pytest.param(-1.5, id="below_negative_one"),
        ],
    )
    def test_invalid_threshold_raises_error(self, invalid_threshold: float) -> None:
        """Threshold outside open interval (-1.0, 1.0) raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AlertingSettings(imbalance_threshold=invalid_threshold)
        assert "imbalance_threshold must be in range (-1.0, 1.0)" in str(exc_info.value)

    def test_custom_cooldown_seconds(self) -> None:
        """Custom cooldown_seconds is accepted."""
        settings = AlertingSettings(imbalance_threshold=0.35, cooldown_seconds=60)
        assert settings.cooldown_seconds == 60

    def test_zero_cooldown_seconds_is_valid(self) -> None:
        """Zero cooldown_seconds (no cooldown) is valid."""
        settings = AlertingSettings(imbalance_threshold=0.35, cooldown_seconds=0)
        assert settings.cooldown_seconds == 0

    def test_negative_cooldown_seconds_raises_error(self) -> None:
        """Negative cooldown_seconds raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AlertingSettings(imbalance_threshold=0.35, cooldown_seconds=-1)
        assert "cooldown_seconds must be non-negative" in str(exc_info.value)

    def test_large_cooldown_seconds_is_valid(self) -> None:
        """Large cooldown_seconds value is valid."""
        settings = AlertingSettings(imbalance_threshold=0.35, cooldown_seconds=3600)
        assert settings.cooldown_seconds == 3600

    def test_settings_are_immutable(self) -> None:
        """Settings object is frozen and cannot be modified."""
        settings = AlertingSettings(imbalance_threshold=0.35)
        with pytest.raises(ValidationError):
            settings.imbalance_threshold = 0.5  # type: ignore[misc]

    def test_very_small_positive_threshold(self) -> None:
        """Very small positive threshold is valid."""
        settings = AlertingSettings(imbalance_threshold=0.001)
        assert settings.imbalance_threshold == 0.001

    def test_very_small_negative_threshold(self) -> None:
        """Very small negative threshold is valid."""
        settings = AlertingSettings(imbalance_threshold=-0.001)
        assert settings.imbalance_threshold == -0.001
