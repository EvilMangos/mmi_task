"""Shared pytest fixtures for config package tests.

This module provides fixtures that simplify environment variable mocking
for Settings tests.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import patch

import pytest


def make_valid_env() -> dict[str, str]:
    """Create a minimal valid environment variable set.

    Returns:
        Dictionary with all required environment variables set to valid values.
    """
    return {
        "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF",
        "TELEGRAM_CHAT_ID": "-1001234567890",
        "SYMBOLS": "BTCUSDT,DOTUSDT,SOLUSDT",
        "IMBALANCE_THRESHOLD": "0.35",
    }


@contextmanager
def patched_env(
    overrides: dict[str, str] | None = None,
    remove: list[str] | None = None,
) -> Generator[dict[str, str], None, None]:
    """Context manager that patches os.environ with valid config values.

    Creates an isolated environment for Settings tests with:
    - All required environment variables set to valid defaults
    - Optional overrides applied
    - Optional keys removed

    Args:
        overrides: Additional or replacement environment variables.
        remove: Keys to remove from the environment (for testing missing required vars).

    Yields:
        The patched environment dictionary.

    Example:
        with patched_env() as env:
            settings = Settings(_env_file=None)

        with patched_env(overrides={"LOG_LEVEL": "DEBUG"}) as env:
            settings = Settings(_env_file=None)
            assert settings.logging.log_level == "DEBUG"

        with patched_env(remove=["TELEGRAM_BOT_TOKEN"]) as env:
            with pytest.raises(ValidationError):
                Settings(_env_file=None)
    """
    env = make_valid_env()
    if overrides:
        env.update(overrides)
    if remove:
        for key in remove:
            env.pop(key, None)

    with patch.dict(os.environ, env, clear=True):
        yield env


@pytest.fixture
def valid_env() -> dict[str, str]:
    """Fixture providing a valid environment variable dictionary.

    Note: This fixture returns the dictionary but does NOT patch os.environ.
    Use in combination with patch.dict or the patched_env context manager.
    """
    return make_valid_env()
