"""Tests for notifier exception hierarchy.

The exception hierarchy provides structured error handling for notification failures:
- NotifierError: Base exception for all notifier-related errors
- PermanentNotifierError: Non-retryable errors (e.g., 4xx HTTP responses, invalid config)
- TransientNotifierError: Retryable errors (e.g., 5xx HTTP responses, network issues)

Requirements covered:
- R1: NotifierError is the base exception class
- R2: PermanentNotifierError inherits from NotifierError
- R3: TransientNotifierError inherits from NotifierError
- R4: All exceptions preserve their message
- R5: Exceptions can carry optional HTTP status code
- R6: Exceptions can carry optional cause (chained exception)
"""

import pytest

from notifier_telegram.exceptions import (
    NotifierError,
    PermanentNotifierError,
    TransientNotifierError,
)


class TestNotifierErrorBase:
    """Tests for NotifierError base exception."""

    def test_is_exception_subclass(self) -> None:
        """R1: NotifierError is a proper Exception subclass."""
        assert issubclass(NotifierError, Exception)

    def test_can_be_raised(self) -> None:
        """R1: NotifierError can be raised and caught."""
        with pytest.raises(NotifierError):
            raise NotifierError("test error")

    def test_preserves_message(self) -> None:
        """R4: NotifierError preserves error message."""
        error = NotifierError("something went wrong")
        assert str(error) == "something went wrong"

    def test_empty_message(self) -> None:
        """R4: NotifierError handles empty message."""
        error = NotifierError("")
        assert str(error) == ""

    def test_message_with_special_characters(self) -> None:
        """R4: NotifierError handles special characters in message."""
        message = "Error: <tag> 'quoted' \"double\" & special!"
        error = NotifierError(message)
        assert str(error) == message

    def test_can_have_status_code(self) -> None:
        """R5: NotifierError can carry HTTP status code."""
        error = NotifierError("error", status_code=500)
        assert error.status_code == 500

    def test_status_code_defaults_to_none(self) -> None:
        """R5: NotifierError status_code defaults to None."""
        error = NotifierError("error")
        assert error.status_code is None

    def test_can_chain_cause(self) -> None:
        """R6: NotifierError can be chained with original cause."""
        original = ValueError("original error")
        try:
            raise NotifierError("wrapper") from original
        except NotifierError as e:
            assert e.__cause__ is original


class TestPermanentNotifierError:
    """Tests for PermanentNotifierError (non-retryable errors)."""

    def test_inherits_from_notifier_error(self) -> None:
        """R2: PermanentNotifierError is a NotifierError subclass."""
        assert issubclass(PermanentNotifierError, NotifierError)

    def test_is_exception_subclass(self) -> None:
        """R2: PermanentNotifierError is also an Exception subclass."""
        assert issubclass(PermanentNotifierError, Exception)

    def test_can_be_raised(self) -> None:
        """R2: PermanentNotifierError can be raised and caught."""
        with pytest.raises(PermanentNotifierError):
            raise PermanentNotifierError("permanent error")

    def test_can_be_caught_as_notifier_error(self) -> None:
        """R2: PermanentNotifierError can be caught as NotifierError."""
        with pytest.raises(NotifierError):
            raise PermanentNotifierError("permanent error")

    def test_preserves_message(self) -> None:
        """R4: PermanentNotifierError preserves error message."""
        error = PermanentNotifierError("invalid bot token")
        assert str(error) == "invalid bot token"

    def test_can_have_status_code(self) -> None:
        """R5: PermanentNotifierError can carry HTTP status code (e.g., 401, 403, 404)."""
        error = PermanentNotifierError("Unauthorized", status_code=401)
        assert error.status_code == 401

    def test_typical_4xx_status_codes(self) -> None:
        """R5: PermanentNotifierError typically used for 4xx errors (except 429)."""
        error_400 = PermanentNotifierError("Bad Request", status_code=400)
        error_401 = PermanentNotifierError("Unauthorized", status_code=401)
        error_403 = PermanentNotifierError("Forbidden", status_code=403)
        error_404 = PermanentNotifierError("Not Found", status_code=404)
        # Note: 429 (Too Many Requests) is treated as transient in TelegramNotifier

        assert error_400.status_code == 400
        assert error_401.status_code == 401
        assert error_403.status_code == 403
        assert error_404.status_code == 404

    def test_can_chain_cause(self) -> None:
        """R6: PermanentNotifierError can be chained with original cause."""
        original = KeyError("missing_key")
        try:
            raise PermanentNotifierError("config error") from original
        except PermanentNotifierError as e:
            assert e.__cause__ is original

    def test_not_same_type_as_transient(self) -> None:
        """PermanentNotifierError is distinct from TransientNotifierError."""
        error = PermanentNotifierError("error")
        assert not isinstance(error, TransientNotifierError)


class TestTransientNotifierError:
    """Tests for TransientNotifierError (retryable errors)."""

    def test_inherits_from_notifier_error(self) -> None:
        """R3: TransientNotifierError is a NotifierError subclass."""
        assert issubclass(TransientNotifierError, NotifierError)

    def test_is_exception_subclass(self) -> None:
        """R3: TransientNotifierError is also an Exception subclass."""
        assert issubclass(TransientNotifierError, Exception)

    def test_can_be_raised(self) -> None:
        """R3: TransientNotifierError can be raised and caught."""
        with pytest.raises(TransientNotifierError):
            raise TransientNotifierError("transient error")

    def test_can_be_caught_as_notifier_error(self) -> None:
        """R3: TransientNotifierError can be caught as NotifierError."""
        with pytest.raises(NotifierError):
            raise TransientNotifierError("transient error")

    def test_preserves_message(self) -> None:
        """R4: TransientNotifierError preserves error message."""
        error = TransientNotifierError("server temporarily unavailable")
        assert str(error) == "server temporarily unavailable"

    def test_can_have_status_code(self) -> None:
        """R5: TransientNotifierError can carry HTTP status code (e.g., 5xx)."""
        error = TransientNotifierError("Internal Server Error", status_code=500)
        assert error.status_code == 500

    def test_typical_5xx_status_codes(self) -> None:
        """R5: TransientNotifierError typically used for 5xx errors."""
        error_500 = TransientNotifierError("Internal Server Error", status_code=500)
        error_502 = TransientNotifierError("Bad Gateway", status_code=502)
        error_503 = TransientNotifierError("Service Unavailable", status_code=503)
        error_504 = TransientNotifierError("Gateway Timeout", status_code=504)

        assert error_500.status_code == 500
        assert error_502.status_code == 502
        assert error_503.status_code == 503
        assert error_504.status_code == 504

    def test_network_error_no_status_code(self) -> None:
        """R5: Network errors may not have a status code."""
        error = TransientNotifierError("Connection refused")
        assert error.status_code is None

    def test_can_chain_cause(self) -> None:
        """R6: TransientNotifierError can be chained with original cause."""
        original = ConnectionError("connection reset")
        try:
            raise TransientNotifierError("network error") from original
        except TransientNotifierError as e:
            assert e.__cause__ is original

    def test_not_same_type_as_permanent(self) -> None:
        """TransientNotifierError is distinct from PermanentNotifierError."""
        error = TransientNotifierError("error")
        assert not isinstance(error, PermanentNotifierError)


class TestExceptionHierarchyUsage:
    """Tests for typical usage patterns of the exception hierarchy."""

    def test_catch_all_notifier_errors(self) -> None:
        """Catching NotifierError catches both permanent and transient."""
        errors_caught = []

        for error_cls in [PermanentNotifierError, TransientNotifierError]:
            try:
                raise error_cls("test")
            except NotifierError as e:
                errors_caught.append(type(e).__name__)

        assert "PermanentNotifierError" in errors_caught
        assert "TransientNotifierError" in errors_caught

    def test_distinguish_permanent_from_transient(self) -> None:
        """Can distinguish between permanent and transient errors for retry logic."""

        def should_retry(error: NotifierError) -> bool:
            return isinstance(error, TransientNotifierError)

        permanent = PermanentNotifierError("bad request", status_code=400)
        transient = TransientNotifierError("server error", status_code=500)

        assert should_retry(permanent) is False
        assert should_retry(transient) is True

    def test_exception_with_full_context(self) -> None:
        """Exceptions can carry message, status code, and cause together."""
        original = TimeoutError("connection timed out")
        error = TransientNotifierError(
            "Telegram API timeout",
            status_code=504,
        )
        error.__cause__ = original

        assert str(error) == "Telegram API timeout"
        assert error.status_code == 504
        assert error.__cause__ is original
        assert isinstance(error.__cause__, TimeoutError)
