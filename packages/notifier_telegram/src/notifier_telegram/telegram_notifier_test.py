"""Tests for TelegramNotifier class.

TelegramNotifier is an async implementation of the Notifier protocol that sends
alerts to Telegram via the Bot API. It handles HTTP interactions, retries on
transient errors, and converts HTTP errors to appropriate exception types.

Requirements covered:
- R1: Constructor accepts bot_token, chat_id, base_url, max_retries, base_delay
- R2: Constructor validates required parameters
- R3: send_alert makes POST request to correct Telegram API endpoint
- R4: send_alert sends properly formatted message in request body
- R5: Successful response (2xx) completes without error
- R6: 4xx responses raise PermanentNotifierError
- R7: 5xx responses raise TransientNotifierError after exhausting retries
- R8: Network errors raise TransientNotifierError after exhausting retries
- R9: Retry logic uses exponential backoff
- R10: Implements Notifier protocol
"""

import asyncio
from unittest.mock import patch

import pytest
from aiohttp import ClientError
from aioresponses import aioresponses

from notifier_telegram.alert_payload import AlertPayload
from notifier_telegram.exceptions import (
    PermanentNotifierError,
    TransientNotifierError,
)
from notifier_telegram.notifier_protocol import Notifier
from notifier_telegram.telegram_notifier import TelegramNotifier


def _make_payload(
    symbol: str = "BTCUSDT",
    ratio: float = 0.45,
    bid_volume: float = 150000.0,
    ask_volume: float = 85000.0,
    timestamp: float = 1702800000.0,
    threshold: float = 0.35,
) -> AlertPayload:
    """Helper to create AlertPayload with defaults."""
    return AlertPayload(
        symbol=symbol,
        ratio=ratio,
        bid_volume=bid_volume,
        ask_volume=ask_volume,
        timestamp=timestamp,
        threshold=threshold,
    )


class TestTelegramNotifierConstruction:
    """Tests for TelegramNotifier constructor."""

    def test_creates_notifier_with_required_params(self) -> None:
        """R1: Constructor accepts required bot_token and chat_id."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        assert notifier.bot_token == "123456:ABC-DEF"
        assert notifier.chat_id == "-1001234567890"

    def test_creates_notifier_with_all_params(self) -> None:
        """R1: Constructor accepts all optional parameters."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            base_url="https://custom.telegram.api",
            max_retries=5,
            base_delay=2.0,
        )

        assert notifier.bot_token == "123456:ABC-DEF"
        assert notifier.chat_id == "-1001234567890"
        assert notifier.base_url == "https://custom.telegram.api"
        assert notifier.max_retries == 5
        assert notifier.base_delay == 2.0

    def test_default_base_url(self) -> None:
        """R1: Default base_url is official Telegram API."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        assert "api.telegram.org" in notifier.base_url

    def test_default_max_retries(self) -> None:
        """R1: Default max_retries is reasonable (e.g., 3)."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        assert notifier.max_retries >= 1
        assert notifier.max_retries <= 10

    def test_default_base_delay(self) -> None:
        """R1: Default base_delay is reasonable (e.g., 1.0 second)."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        assert notifier.base_delay >= 0.1
        assert notifier.base_delay <= 10.0


class TestTelegramNotifierValidation:
    """Tests for TelegramNotifier input validation."""

    def test_rejects_empty_bot_token(self) -> None:
        """R2: Empty bot_token raises ValueError."""
        with pytest.raises(ValueError, match="bot_token"):
            TelegramNotifier(
                bot_token="",
                chat_id="-1001234567890",
            )

    def test_rejects_whitespace_bot_token(self) -> None:
        """R2: Whitespace-only bot_token raises ValueError."""
        with pytest.raises(ValueError, match="bot_token"):
            TelegramNotifier(
                bot_token="   ",
                chat_id="-1001234567890",
            )

    def test_rejects_empty_chat_id(self) -> None:
        """R2: Empty chat_id raises ValueError."""
        with pytest.raises(ValueError, match="chat_id"):
            TelegramNotifier(
                bot_token="123456:ABC-DEF",
                chat_id="",
            )

    def test_rejects_whitespace_chat_id(self) -> None:
        """R2: Whitespace-only chat_id raises ValueError."""
        with pytest.raises(ValueError, match="chat_id"):
            TelegramNotifier(
                bot_token="123456:ABC-DEF",
                chat_id="   ",
            )

    def test_rejects_negative_max_retries(self) -> None:
        """R2: Negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries"):
            TelegramNotifier(
                bot_token="123456:ABC-DEF",
                chat_id="-1001234567890",
                max_retries=-1,
            )

    def test_rejects_negative_base_delay(self) -> None:
        """R2: Negative base_delay raises ValueError."""
        with pytest.raises(ValueError, match="base_delay"):
            TelegramNotifier(
                bot_token="123456:ABC-DEF",
                chat_id="-1001234567890",
                base_delay=-1.0,
            )

    def test_accepts_zero_max_retries(self) -> None:
        """R2: Zero max_retries is valid (no retries)."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )

        assert notifier.max_retries == 0

    def test_accepts_zero_base_delay(self) -> None:
        """R2: Zero base_delay is valid (immediate retries)."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            base_delay=0.0,
        )

        assert notifier.base_delay == 0.0


class TestTelegramNotifierProtocolCompliance:
    """Tests for Notifier protocol compliance."""

    def test_implements_notifier_protocol(self) -> None:
        """R10: TelegramNotifier implements Notifier protocol."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        assert isinstance(notifier, Notifier)

    def test_has_send_alert_method(self) -> None:
        """R10: TelegramNotifier has send_alert method."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        assert hasattr(notifier, "send_alert")
        assert callable(notifier.send_alert)

    def test_send_alert_is_coroutine(self) -> None:
        """R10: send_alert is an async method."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        # Check it returns a coroutine when called
        payload = _make_payload()
        result = notifier.send_alert(payload)
        assert asyncio.iscoroutine(result)
        # Clean up the coroutine
        result.close()


@pytest.mark.asyncio
class TestTelegramNotifierSendAlertSuccess:
    """Tests for successful send_alert scenarios."""

    async def test_sends_post_to_correct_endpoint(self) -> None:
        """R3: send_alert makes POST to /bot<token>/sendMessage."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})

            await notifier.send_alert(payload)

            # Verify the request was made to the correct URL
            mocked.assert_called_once()
            # The key in mocked.requests is a tuple (method, URL)
            request_keys = list(mocked.requests.keys())
            assert len(request_keys) == 1
            method, url = request_keys[0]
            assert method == "POST"
            assert str(url) == expected_url

    async def test_sends_chat_id_in_request(self) -> None:
        """R4: Request body contains chat_id."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})

            await notifier.send_alert(payload)

            # Get the request kwargs from mocked.requests
            # Structure: {(method, url): [(method, kwargs_dict), ...]}
            calls = list(mocked.requests.values())[0]
            call_info = calls[0]  # First call
            # call_info is (method, kwargs_dict)
            request_kwargs = call_info[1] if len(call_info) > 1 else call_info
            if isinstance(request_kwargs, str):
                # If it's the method string, the structure is different
                request_kwargs = {}
            request_data = request_kwargs.get("json") or request_kwargs.get("data")

            assert request_data is not None
            assert request_data.get("chat_id") == "-1001234567890"

    async def test_sends_text_in_request(self) -> None:
        """R4: Request body contains text message."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload(symbol="ETHUSDT")

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})

            await notifier.send_alert(payload)

            # Get the request data from mocked.requests
            calls = list(mocked.requests.values())[0]
            call_info = calls[0]  # First call
            request_kwargs = call_info[1] if len(call_info) > 1 else call_info
            if isinstance(request_kwargs, str):
                request_kwargs = {}
            request_data = request_kwargs.get("json") or request_kwargs.get("data")

            assert request_data is not None
            assert "text" in request_data
            assert len(request_data["text"]) > 0
            # The symbol should appear in the message
            assert "ETHUSDT" in request_data["text"]

    async def test_success_returns_without_error(self) -> None:
        """R5: 200 OK response completes without raising."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})

            # Should not raise
            await notifier.send_alert(payload)

    async def test_201_response_is_success(self) -> None:
        """R5: Other 2xx responses are also successful."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=201, payload={"ok": True})

            # Should not raise
            await notifier.send_alert(payload)

    async def test_uses_custom_base_url(self) -> None:
        """R3: Custom base_url is used for request."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            base_url="https://custom.api.example.com",
        )
        payload = _make_payload()

        expected_url = "https://custom.api.example.com/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})

            await notifier.send_alert(payload)

            mocked.assert_called_once()


@pytest.mark.asyncio
class TestTelegramNotifierPermanentErrors:
    """Tests for permanent (4xx) error handling."""

    async def test_400_raises_permanent_error(self) -> None:
        """R6: 400 Bad Request raises PermanentNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=400, payload={"ok": False})

            with pytest.raises(PermanentNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 400

    async def test_401_raises_permanent_error(self) -> None:
        """R6: 401 Unauthorized raises PermanentNotifierError."""
        notifier = TelegramNotifier(
            bot_token="invalid_token",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/botinvalid_token/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=401, payload={"ok": False})

            with pytest.raises(PermanentNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 401

    async def test_403_raises_permanent_error(self) -> None:
        """R6: 403 Forbidden raises PermanentNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="invalid_chat",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=403, payload={"ok": False})

            with pytest.raises(PermanentNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 403

    async def test_404_raises_permanent_error(self) -> None:
        """R6: 404 Not Found raises PermanentNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=404, payload={"ok": False})

            with pytest.raises(PermanentNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 404

    async def test_4xx_errors_not_retried(self) -> None:
        """R6: 4xx errors are not retried."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=3,
            base_delay=0.0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            # Only add one response - if retries happen, it will fail differently
            mocked.post(expected_url, status=400, payload={"ok": False})

            with pytest.raises(PermanentNotifierError):
                await notifier.send_alert(payload)

            # Verify only one request was made
            assert len(list(mocked.requests.values())[0]) == 1


@pytest.mark.asyncio
class TestTelegramNotifierTransientErrors:
    """Tests for transient (5xx, network) error handling and retries."""

    async def test_500_raises_transient_error_after_retries(self) -> None:
        """R7: 500 error raises TransientNotifierError after exhausting retries."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=2,
            base_delay=0.0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            # Add enough responses for initial + retries
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})

            with pytest.raises(TransientNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 500

    async def test_502_raises_transient_error(self) -> None:
        """R7: 502 Bad Gateway raises TransientNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=502, payload={"ok": False})

            with pytest.raises(TransientNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 502

    async def test_503_raises_transient_error(self) -> None:
        """R7: 503 Service Unavailable raises TransientNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=503, payload={"ok": False})

            with pytest.raises(TransientNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 503

    async def test_504_raises_transient_error(self) -> None:
        """R7: 504 Gateway Timeout raises TransientNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=504, payload={"ok": False})

            with pytest.raises(TransientNotifierError) as exc_info:
                await notifier.send_alert(payload)

            assert exc_info.value.status_code == 504

    async def test_5xx_errors_are_retried(self) -> None:
        """R7: 5xx errors trigger retries."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=2,
            base_delay=0.0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            # First two fail, third succeeds
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=200, payload={"ok": True})

            # Should eventually succeed
            await notifier.send_alert(payload)

            # Verify 3 requests were made (initial + 2 retries)
            assert len(list(mocked.requests.values())[0]) == 3

    async def test_network_error_raises_transient_error(self) -> None:
        """R8: Network errors raise TransientNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, exception=ClientError("Connection refused"))

            with pytest.raises(TransientNotifierError):
                await notifier.send_alert(payload)

    async def test_network_error_is_retried(self) -> None:
        """R8: Network errors trigger retries."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=2,
            base_delay=0.0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            # First two fail with network error, third succeeds
            mocked.post(expected_url, exception=ClientError("Connection refused"))
            mocked.post(expected_url, exception=ClientError("Connection refused"))
            mocked.post(expected_url, status=200, payload={"ok": True})

            # Should eventually succeed
            await notifier.send_alert(payload)

            # Verify retries happened
            assert len(list(mocked.requests.values())[0]) == 3

    async def test_timeout_error_raises_transient_error(self) -> None:
        """R8: Timeout errors raise TransientNotifierError."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, exception=asyncio.TimeoutError())

            with pytest.raises(TransientNotifierError):
                await notifier.send_alert(payload)


@pytest.mark.asyncio
class TestTelegramNotifierRetryBackoff:
    """Tests for exponential backoff behavior during retries."""

    async def test_retry_uses_exponential_backoff(self) -> None:
        """R9: Retries use exponential backoff (delay doubles each retry)."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=3,
            base_delay=0.1,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        sleep_calls: list[float] = []

        async def mock_sleep(delay: float) -> None:
            sleep_calls.append(delay)
            # Don't actually sleep in tests

        with aioresponses() as mocked:
            # All requests fail
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})

            with patch("asyncio.sleep", mock_sleep):
                with pytest.raises(TransientNotifierError):
                    await notifier.send_alert(payload)

        # Verify exponential backoff pattern
        # Expected delays: 0.1, 0.2, 0.4 (or similar exponential pattern)
        assert len(sleep_calls) == 3  # One sleep per retry
        # Each delay should be >= previous (exponential)
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] >= sleep_calls[i - 1]

    async def test_no_retry_means_no_sleep(self) -> None:
        """R9: With max_retries=0, no sleep is called."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        sleep_called = False

        async def mock_sleep(delay: float) -> None:
            nonlocal sleep_called
            sleep_called = True

        with aioresponses() as mocked:
            mocked.post(expected_url, status=500, payload={"ok": False})

            with patch("asyncio.sleep", mock_sleep):
                with pytest.raises(TransientNotifierError):
                    await notifier.send_alert(payload)

        assert not sleep_called


@pytest.mark.asyncio
class TestTelegramNotifierErrorMessages:
    """Tests for error message quality in exceptions."""

    async def test_permanent_error_includes_status_description(self) -> None:
        """PermanentNotifierError message includes useful context."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(
                expected_url,
                status=400,
                payload={"ok": False, "description": "Bad Request: chat not found"},
            )

            with pytest.raises(PermanentNotifierError) as exc_info:
                await notifier.send_alert(payload)

            error_message = str(exc_info.value)
            # Should contain some useful info
            assert "400" in error_message or "Bad Request" in error_message.lower()

    async def test_transient_error_includes_retry_info(self) -> None:
        """TransientNotifierError message may include retry context."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
            max_retries=2,
            base_delay=0.0,
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})
            mocked.post(expected_url, status=500, payload={"ok": False})

            with pytest.raises(TransientNotifierError) as exc_info:
                await notifier.send_alert(payload)

            # Error should exist and have meaningful content
            assert str(exc_info.value)


@pytest.mark.asyncio
class TestTelegramNotifierEdgeCases:
    """Tests for edge cases and boundary conditions."""

    async def test_handles_empty_response_body(self) -> None:
        """Handles responses with no JSON body."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            # Empty response body but success status
            mocked.post(expected_url, status=200, body="")

            # Should handle gracefully
            await notifier.send_alert(payload)

    async def test_handles_malformed_json_response(self) -> None:
        """Handles responses with invalid JSON."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        payload = _make_payload()

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, body="not json")

            # Should handle gracefully (success status = success)
            await notifier.send_alert(payload)

    async def test_multiple_alerts_can_be_sent(self) -> None:
        """Multiple alerts can be sent sequentially."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})
            mocked.post(expected_url, status=200, payload={"ok": True})
            mocked.post(expected_url, status=200, payload={"ok": True})

            await notifier.send_alert(_make_payload(symbol="BTCUSDT"))
            await notifier.send_alert(_make_payload(symbol="ETHUSDT"))
            await notifier.send_alert(_make_payload(symbol="SOLUSDT"))

            assert len(list(mocked.requests.values())[0]) == 3

    async def test_special_characters_in_alert_payload(self) -> None:
        """Alert with special characters in symbol is handled."""
        notifier = TelegramNotifier(
            bot_token="123456:ABC-DEF",
            chat_id="-1001234567890",
        )
        # Some exchanges have unusual symbol formats
        payload = _make_payload(symbol="1000SHIBUSDT")

        expected_url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

        with aioresponses() as mocked:
            mocked.post(expected_url, status=200, payload={"ok": True})

            await notifier.send_alert(payload)
