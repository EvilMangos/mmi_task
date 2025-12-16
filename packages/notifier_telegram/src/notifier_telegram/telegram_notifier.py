"""TelegramNotifier implementation.

TelegramNotifier is an async implementation of the Notifier protocol that sends
alerts to Telegram via the Bot API. It handles HTTP interactions, retries on
transient errors, and converts HTTP errors to appropriate exception types.
"""

import asyncio
from types import TracebackType
from typing import Self

import aiohttp

from notifier_telegram.alert_payload import AlertPayload
from notifier_telegram.exceptions import PermanentNotifierError, TransientNotifierError
from notifier_telegram.message_formatter import format_alert_message

# Default configuration constants
_DEFAULT_TIMEOUT_SECONDS = 10
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BASE_DELAY_SECONDS = 1.0


def _validate_non_empty_string(value: str, name: str) -> None:
    """Validate that a string is not empty or whitespace-only.

    Args:
        value: The string value to validate.
        name: The parameter name for the error message.

    Raises:
        ValueError: If value is empty or contains only whitespace.
    """
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty or whitespace")


def _validate_non_negative(value: int | float, name: str) -> None:
    """Validate that a numeric value is not negative.

    Args:
        value: The numeric value to validate.
        name: The parameter name for the error message.

    Raises:
        ValueError: If value is negative.
    """
    if value < 0:
        raise ValueError(f"{name} must not be negative")


def _is_success_status(status: int) -> bool:
    """Check if HTTP status indicates success (2xx)."""
    return 200 <= status < 300


def _is_retryable_status(status: int) -> bool:
    """Check if HTTP status indicates a retryable error (429 or 5xx)."""
    return status == 429 or status >= 500


def _is_permanent_error_status(status: int) -> bool:
    """Check if HTTP status indicates a permanent error (4xx except 429)."""
    return 400 <= status < 500 and status != 429


def _create_retry_exhausted_error(
    last_exception: Exception | None,
    last_status_code: int | None,
    max_retries: int,
) -> TransientNotifierError:
    """Create a TransientNotifierError after all retries are exhausted.

    Args:
        last_exception: The last network/timeout exception, if any.
        last_status_code: The last HTTP status code, if any.
        max_retries: The maximum number of retries attempted.

    Returns:
        A TransientNotifierError with appropriate message and cause.
    """
    if last_exception is not None:
        error = TransientNotifierError(
            f"Network error after {max_retries} retries: {last_exception}",
            status_code=None,
        )
        error.__cause__ = last_exception
        return error
    else:
        return TransientNotifierError(
            f"Telegram API error after {max_retries} retries: HTTP {last_status_code}",
            status_code=last_status_code,
        )


class TelegramNotifier:
    """Telegram Bot API notifier implementation.

    Sends alert messages to Telegram chats via the Bot API.
    Implements retry logic with exponential backoff for transient errors.

    The notifier manages an HTTP session internally. It can be used in two ways:
    1. As a context manager: async with TelegramNotifier(...) as notifier: ...
    2. With explicit lifecycle: await notifier.start(); ...; await notifier.stop()

    If used without explicit lifecycle management, creates a new session per request
    (less efficient but works for simple use cases).
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        base_url: str = "https://api.telegram.org",
        max_retries: int = _DEFAULT_MAX_RETRIES,
        base_delay: float = _DEFAULT_BASE_DELAY_SECONDS,
    ) -> None:
        """Initialize TelegramNotifier.

        Args:
            bot_token: Telegram bot token.
            chat_id: Target chat/channel ID.
            base_url: Base URL for Telegram API (default: official API).
            max_retries: Maximum number of retry attempts for transient errors.
            base_delay: Base delay in seconds for exponential backoff.

        Raises:
            ValueError: If bot_token/chat_id is empty or max_retries/base_delay is negative.
        """
        _validate_non_empty_string(bot_token, "bot_token")
        _validate_non_empty_string(chat_id, "chat_id")
        _validate_non_negative(max_retries, "max_retries")
        _validate_non_negative(base_delay, "base_delay")

        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = base_url
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._session: aiohttp.ClientSession | None = None
        self._owns_session = False

    async def start(self) -> None:
        """Start the notifier and create the HTTP session.

        Call this before sending alerts if not using the context manager.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=_DEFAULT_TIMEOUT_SECONDS)
            )
            self._owns_session = True

    async def stop(self) -> None:
        """Stop the notifier and close the HTTP session.

        Call this when done sending alerts if not using the context manager.
        """
        if self._session is not None and self._owns_session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._owns_session = False

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager."""
        await self.stop()

    @property
    def bot_token(self) -> str:
        """Return the bot token."""
        return self._bot_token

    @property
    def chat_id(self) -> str:
        """Return the chat ID."""
        return self._chat_id

    @property
    def base_url(self) -> str:
        """Return the base URL."""
        return self._base_url

    @property
    def max_retries(self) -> int:
        """Return the maximum number of retries."""
        return self._max_retries

    @property
    def base_delay(self) -> float:
        """Return the base delay for exponential backoff."""
        return self._base_delay

    async def send_alert(self, alert: AlertPayload) -> None:
        """Send an imbalance alert to Telegram.

        Args:
            alert: The alert payload to send.

        Raises:
            PermanentNotifierError: For 4xx HTTP errors (non-retryable).
            TransientNotifierError: For 5xx/network errors after exhausting retries.
        """
        url = f"{self._base_url}/bot{self._bot_token}/sendMessage"
        message_text = format_alert_message(alert)
        payload = {
            "chat_id": self._chat_id,
            "text": message_text,
        }

        # Use existing session if available, otherwise create temporary one
        if self._session is not None and not self._session.closed:
            await self._send_with_retry(url, payload, self._session)
        else:
            # Fallback: create a temporary session per request (less efficient)
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=_DEFAULT_TIMEOUT_SECONDS)
            ) as session:
                await self._send_with_retry(url, payload, session)

    async def _send_with_retry(
        self,
        url: str,
        payload: dict[str, str],
        session: aiohttp.ClientSession,
    ) -> None:
        """Send request with retry logic using the provided session."""
        last_exception: Exception | None = None
        last_status_code: int | None = None

        for attempt in range(self._max_retries + 1):
            try:
                async with session.post(url, json=payload) as response:
                    status = response.status

                    if _is_success_status(status):
                        return

                    if _is_permanent_error_status(status):
                        raise PermanentNotifierError(
                            f"Telegram API error: HTTP {status}",
                            status_code=status,
                        )

                    # Retryable status (429 or 5xx) - record and continue to retry
                    last_status_code = status
                    last_exception = None

            except PermanentNotifierError:
                # Re-raise permanent errors immediately
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Network/timeout errors are transient
                last_exception = e
                last_status_code = None

            # Apply exponential backoff before retry (if not last attempt)
            if attempt < self._max_retries:
                delay = self._base_delay * (2**attempt)
                await asyncio.sleep(delay)

        # All retries exhausted - raise transient error
        raise _create_retry_exhausted_error(last_exception, last_status_code, self._max_retries)
