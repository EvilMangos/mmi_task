"""Tests for timing helper."""

from __future__ import annotations

import time
from typing import Any

import pytest

from observability.timing import timed


class TestTimedContextManager:
    """Tests for timed context manager usage."""

    def test_timed_context_manager_measures_elapsed(self) -> None:
        """Context manager measures elapsed time in seconds."""
        with timed("test_operation") as timer:
            time.sleep(0.1)

        # Should have elapsed_seconds attribute after exit
        assert hasattr(timer, "elapsed_seconds")
        assert timer.elapsed_seconds >= 0.1
        assert timer.elapsed_seconds < 0.5  # Reasonable upper bound

    def test_timed_context_manager_calls_callback(self) -> None:
        """Context manager calls on_complete callback with name and duration."""
        callback_calls: list[tuple[str, float]] = []

        def on_complete(name: str, elapsed: float) -> None:
            callback_calls.append((name, elapsed))

        with timed("my_operation", on_complete=on_complete):
            time.sleep(0.05)

        assert len(callback_calls) == 1
        name, elapsed = callback_calls[0]
        assert name == "my_operation"
        assert elapsed >= 0.05

    def test_timed_handles_exception(self) -> None:
        """Context manager still records time even when exception occurs."""
        callback_calls: list[tuple[str, float]] = []

        def on_complete(name: str, elapsed: float) -> None:
            callback_calls.append((name, elapsed))

        with pytest.raises(ValueError):
            with timed("failing_operation", on_complete=on_complete):
                time.sleep(0.05)
                raise ValueError("Test error")

        # Callback should still be called
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "failing_operation"
        assert callback_calls[0][1] >= 0.05


class TestTimedDecorator:
    """Tests for timed decorator usage."""

    def test_timed_decorator_measures_function(self) -> None:
        """Decorator measures function execution time."""
        callback_calls: list[tuple[str, float]] = []

        def on_complete(name: str, elapsed: float) -> None:
            callback_calls.append((name, elapsed))

        @timed("my_function", on_complete=on_complete)
        def slow_function() -> str:
            time.sleep(0.05)
            return "done"

        result = slow_function()

        assert result == "done"
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "my_function"
        assert callback_calls[0][1] >= 0.05

    def test_timed_decorator_preserves_return_value(self) -> None:
        """Decorator preserves the function's return value."""
        @timed("returning_function")
        def compute() -> dict[str, Any]:
            return {"answer": 42, "valid": True}

        result = compute()

        assert result == {"answer": 42, "valid": True}

    def test_timed_decorator_preserves_exception(self) -> None:
        """Decorator re-raises exceptions from the decorated function."""
        @timed("failing_function")
        def failing() -> None:
            raise RuntimeError("Expected error")

        with pytest.raises(RuntimeError, match="Expected error"):
            failing()

    def test_timed_decorator_with_arguments(self) -> None:
        """Decorator works with functions that have arguments."""
        @timed("add_function")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(3, 4)

        assert result == 7

    def test_timed_decorator_with_kwargs(self) -> None:
        """Decorator works with functions that have keyword arguments."""
        @timed("greet_function")
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        result = greet("World", greeting="Hi")

        assert result == "Hi, World!"
