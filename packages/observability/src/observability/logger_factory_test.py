"""Tests for logger factory."""

from __future__ import annotations

import json
import logging
from io import StringIO

import pytest


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger_instance(self) -> None:
        """get_logger returns a logging.Logger instance."""
        from observability.logger_factory import get_logger

        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_respects_log_level_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Logger level is set based on LOG_LEVEL environment variable."""
        from observability.logger_factory import get_logger

        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        # Need a unique name to avoid cached logger
        logger = get_logger("test.env.debug")

        assert (
            logger.level == logging.DEBUG or logger.getEffectiveLevel() == logging.DEBUG
        )

    def test_get_logger_defaults_to_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When LOG_LEVEL is not set, logger defaults to INFO level."""
        from observability.logger_factory import get_logger

        monkeypatch.delenv("LOG_LEVEL", raising=False)

        # Unique name
        logger = get_logger("test.default.level")

        effective_level = logger.getEffectiveLevel()
        assert effective_level == logging.INFO

    def test_get_logger_same_name_returns_same_logger(self) -> None:
        """Calling get_logger with the same name returns the same logger instance."""
        from observability.logger_factory import get_logger

        logger1 = get_logger("test.same.name")
        logger2 = get_logger("test.same.name")

        assert logger1 is logger2

    def test_logger_outputs_json(self, capfd: pytest.CaptureFixture[str]) -> None:
        """Logger output is valid JSON format."""
        from observability.json_formatter import JsonFormatter
        from observability.logger_factory import get_logger

        # Create a unique logger
        logger = get_logger("test.json.output.capture")

        # Add a handler that writes to stderr (which capfd captures)
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            logger.info("Test JSON output")
            handler.flush()
            output = stream.getvalue().strip()

            # Should be valid JSON
            assert output != ""
            parsed = json.loads(output)
            assert isinstance(parsed, dict)
            assert parsed.get("message") == "Test JSON output"
        finally:
            logger.removeHandler(handler)
