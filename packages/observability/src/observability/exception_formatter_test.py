"""Tests for exception formatter."""

from __future__ import annotations


class TestFormatException:
    """Tests for format_exception function."""

    def test_format_exception_includes_type(self) -> None:
        """Formatted exception includes the exception type name."""
        from observability.exception_formatter import format_exception

        try:
            raise ValueError("test error")
        except ValueError as exc:
            result = format_exception(exc)

        assert "type" in result
        assert result["type"] == "ValueError"

    def test_format_exception_includes_message(self) -> None:
        """Formatted exception includes the exception message."""
        from observability.exception_formatter import format_exception

        try:
            raise RuntimeError("Something went wrong")
        except RuntimeError as exc:
            result = format_exception(exc)

        assert "message" in result
        assert result["message"] == "Something went wrong"

    def test_format_exception_includes_traceback(self) -> None:
        """Formatted exception includes the traceback string."""
        from observability.exception_formatter import format_exception

        try:
            raise KeyError("missing_key")
        except KeyError as exc:
            result = format_exception(exc)

        assert "traceback" in result
        traceback_str = result["traceback"]
        assert isinstance(traceback_str, str)
        # Traceback should include the file and the raise statement
        assert "KeyError" in traceback_str
        assert "missing_key" in traceback_str

    def test_format_exception_handles_chained(self) -> None:
        """Formatted exception includes info about chained exceptions."""
        from observability.exception_formatter import format_exception

        try:
            try:
                raise ValueError("original error")
            except ValueError as original:
                raise RuntimeError("wrapper error") from original
        except RuntimeError as exc:
            result = format_exception(exc)

        # Should have main exception info
        assert result["type"] == "RuntimeError"
        assert result["message"] == "wrapper error"

        # The traceback should include the original exception
        traceback_str = result["traceback"]
        assert "ValueError" in traceback_str
        assert "original error" in traceback_str


class TestFormatExceptionEdgeCases:
    """Tests for edge cases in exception formatting."""

    def test_format_exception_empty_message(self) -> None:
        """Exception with empty message is handled."""
        from observability.exception_formatter import format_exception

        try:
            raise ValueError()
        except ValueError as exc:
            result = format_exception(exc)

        assert result["type"] == "ValueError"
        assert result["message"] == ""

    def test_format_exception_custom_exception(self) -> None:
        """Custom exception classes are handled correctly."""
        from observability.exception_formatter import format_exception

        class CustomError(Exception):
            pass

        try:
            raise CustomError("custom message")
        except CustomError as exc:
            result = format_exception(exc)

        assert result["type"] == "CustomError"
        assert result["message"] == "custom message"

    def test_format_exception_with_args(self) -> None:
        """Exception with multiple args is handled."""
        from observability.exception_formatter import format_exception

        try:
            raise ValueError("arg1", "arg2", 42)
        except ValueError as exc:
            result = format_exception(exc)

        assert result["type"] == "ValueError"
        # Message should contain the args in some form
        message = result["message"]
        assert "arg1" in message or str(("arg1", "arg2", 42)) in message
