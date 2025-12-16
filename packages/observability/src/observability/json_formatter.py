"""JSON log formatter for structured logging."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from observability.correlation import get_correlation_id
from observability.exception_formatter import format_exception


class JsonFormatter(logging.Formatter):
    """A logging formatter that outputs JSON-structured log records."""

    # Standard LogRecord attributes that should not be included in extras
    _RESERVED_ATTRS = frozenset(
        {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        The output includes:
        - timestamp: ISO8601 format with timezone
        - level: Log level name
        - logger: Logger name
        - message: Formatted log message
        - correlation_id: Current correlation ID (if set)
        - extra: Any additional fields passed to the log call
        - exception: Formatted exception info (if present)

        Args:
            record: The log record to format.

        Returns:
            A JSON string representation of the log record.
        """
        # Get the formatted message
        message = record.getMessage()

        # Build timestamp in ISO8601 format
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        # Build the base log entry
        log_entry: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "correlation_id": get_correlation_id(),
        }

        # Extract extra fields (non-standard attributes)
        extra: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key not in self._RESERVED_ATTRS:
                extra[key] = value

        if extra:
            log_entry["extra"] = extra

        # Handle exception info
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = format_exception(record.exc_info[1])

        return json.dumps(log_entry)
