"""Logger factory for creating configured loggers."""

import logging
import os
import sys

from observability.json_formatter import JsonFormatter


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger with JSON formatting.

    Creates or retrieves a logger with the given name, configured with:
    - Log level from LOG_LEVEL environment variable (defaults to INFO)
    - JSON formatter for structured output
    - StreamHandler for stdout output

    Args:
        name: The name for the logger.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Determine log level from environment
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Only add handler if the logger doesn't already have one
    # (to avoid duplicate handlers on repeated calls)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger
