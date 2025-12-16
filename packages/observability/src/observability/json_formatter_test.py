"""Tests for JSON log formatter."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from observability.correlation import correlation_context
from observability.json_formatter import JsonFormatter


class TestJsonFormatterFormat:
    """Tests for JsonFormatter.format method."""

    def test_format_produces_valid_json(self) -> None:
        """Format method returns a valid JSON string."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_includes_required_fields(self) -> None:
        """Formatted output includes timestamp, level, logger, and message."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="myapp.module",
            level=logging.WARNING,
            pathname="module.py",
            lineno=100,
            msg="Something happened",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "timestamp" in parsed
        assert "level" in parsed
        assert parsed["level"] == "WARNING"
        assert "logger" in parsed
        assert parsed["logger"] == "myapp.module"
        assert "message" in parsed
        assert parsed["message"] == "Something happened"

    def test_format_includes_correlation_id_when_set(self) -> None:
        """When correlation ID is set, it appears in the formatted output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="With correlation",
            args=(),
            exc_info=None,
        )

        with correlation_context("corr-id-789"):
            result = formatter.format(record)

        parsed = json.loads(result)
        assert parsed.get("correlation_id") == "corr-id-789"

    def test_format_excludes_correlation_id_when_not_set(self) -> None:
        """When no correlation ID is set, correlation_id field is null."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="No correlation",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        # The field should exist but be null
        assert "correlation_id" in parsed
        assert parsed["correlation_id"] is None

    def test_format_includes_extra_fields(self) -> None:
        """Extra fields passed to the log record appear in the output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="With extras",
            args=(),
            exc_info=None,
        )
        # Add extra fields
        record.user_id = "user-123"
        record.request_id = "req-456"

        result = formatter.format(record)
        parsed = json.loads(result)

        # Extra fields should be in an 'extra' dict or at top level
        extra = parsed.get("extra", parsed)
        assert extra.get("user_id") == "user-123" or parsed.get("user_id") == "user-123"
        assert extra.get("request_id") == "req-456" or parsed.get("request_id") == "req-456"

    def test_format_includes_exception_info(self) -> None:
        """When exc_info is present, exception details are included."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="An error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        # Should have exception info
        assert "exception" in parsed or "exc_info" in parsed or "traceback" in parsed
        exc_data = parsed.get("exception") or parsed.get("exc_info") or parsed.get("traceback")
        assert exc_data is not None

    def test_format_timestamp_is_iso8601(self) -> None:
        """Timestamp in the output is in ISO 8601 format."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Check timestamp",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        timestamp_str = parsed["timestamp"]
        # Should be parseable as ISO 8601
        # Common formats: "2024-01-15T10:30:00.123456" or "2024-01-15T10:30:00.123456Z"
        # Try parsing - should not raise
        try:
            datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            # Try alternative format
            datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
