"""Exception hierarchy for notifier errors.

The exception hierarchy provides structured error handling for notification failures:
- NotifierError: Base exception for all notifier-related errors
- PermanentNotifierError: Non-retryable errors (e.g., 4xx HTTP responses, invalid config)
- TransientNotifierError: Retryable errors (e.g., 5xx HTTP responses, network issues)

These exceptions extend the base contracts exceptions with Telegram-specific
attributes like HTTP status codes.
"""

from contracts import (
    NotifierError as BaseNotifierError,
    PermanentNotifierError as BasePermanentNotifierError,
    TransientNotifierError as BaseTransientNotifierError,
)


class NotifierError(BaseNotifierError):
    """Base exception for all notifier-related errors.

    Extends the contracts NotifierError with HTTP status code tracking.

    Attributes:
        status_code: Optional HTTP status code associated with the error.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize NotifierError.

        Args:
            message: Human-readable error description.
            status_code: Optional HTTP status code.
        """
        super().__init__(message)
        self.status_code = status_code


class PermanentNotifierError(NotifierError, BasePermanentNotifierError):
    """Non-retryable notifier error.

    Raised for errors that will not succeed on retry, such as:
    - 4xx HTTP responses (bad request, unauthorized, forbidden, not found)
    - Invalid configuration
    - Invalid input data
    """

    pass


class TransientNotifierError(NotifierError, BaseTransientNotifierError):
    """Retryable notifier error.

    Raised for errors that may succeed on retry, such as:
    - 5xx HTTP responses (server error, bad gateway, service unavailable)
    - Network connectivity issues
    - Timeouts
    """

    pass
