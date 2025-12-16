"""Exception formatting utilities for structured logging."""

import traceback
from typing import Any


def format_exception(exc: BaseException) -> dict[str, Any]:
    """Format an exception into a structured dictionary.

    Args:
        exc: The exception to format.

    Returns:
        A dictionary with keys:
        - type: The exception class name
        - message: The string representation of the exception
        - traceback: The formatted traceback string (includes chained exceptions)
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)
    exc_traceback = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )

    return {
        "type": exc_type,
        "message": exc_message,
        "traceback": exc_traceback,
    }
