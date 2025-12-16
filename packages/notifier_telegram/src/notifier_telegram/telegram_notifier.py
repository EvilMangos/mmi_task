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

# Default HTTP timeout for Telegram API calls (10 seconds)
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10)


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
        max_retries: int = 3,
        base_delay: float = 1.0,
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
        if not bot_token or not bot_token.strip():
            raise ValueError("bot_token must not be empty or whitespace")
        if not chat_id or not chat_id.strip():
            raise ValueError("chat_id must not be empty or whitespace")
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if base_delay < 0:
            raise ValueError("base_delay must not be negative")

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
            self._session = aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT)
            self._owns_session = True

    async def stop(self) -> None:
        """Stop the notifier and close the HTTP session.

        Call this when done sending alerts if not using the context manager.
        """
        if (
            self._session is not None
            and self._owns_session
            and not self._session.closed
        ):
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
            async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
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

                    # Success case
                    if 200 <= status < 300:
                        return

                    # Rate limiting (429) - transient, should retry
                    if status == 429:
                        last_status_code = status
                        last_exception = None
                    # Client error (4xx except 429) - permanent, do not retry
                    elif 400 <= status < 500:
                        raise PermanentNotifierError(
                            f"Telegram API error: HTTP {status}",
                            status_code=status,
                        )
                    # Server error (5xx) - transient, may retry
                    else:
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
        if last_exception is not None:
            raise TransientNotifierError(
                f"Network error after {self._max_retries} retries: {last_exception}",
                status_code=None,
            ) from last_exception
        else:
            raise TransientNotifierError(
                f"Telegram API error after {self._max_retries} retries: HTTP {last_status_code}",
                status_code=last_status_code,
            )
