"""Timing utilities for performance measurement."""

import time
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class timed:
    """A context manager and decorator for timing code execution.

    Can be used as a context manager:
        with timed("operation") as t:
            do_work()
        print(t.elapsed_seconds)

    Or as a decorator:
        @timed("my_function")
        def my_function():
            pass

    Args:
        name: A descriptive name for the timed operation.
        on_complete: Optional callback called with (name, elapsed_seconds) on completion.
    """

    def __init__(
        self,
        name: str,
        on_complete: Callable[[str, float], None] | None = None,
    ) -> None:
        self.name = name
        self.on_complete = on_complete
        self._start_time: float | None = None
        self._elapsed_seconds: float | None = None

    @property
    def elapsed_seconds(self) -> float:
        """Get the elapsed time in seconds.

        Raises:
            RuntimeError: If accessed before the timed block has completed.
        """
        if self._elapsed_seconds is None:
            raise RuntimeError(
                "elapsed_seconds is not available until the timed block completes"
            )
        return self._elapsed_seconds

    def __enter__(self) -> "timed":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._start_time is not None:
            self._elapsed_seconds = time.perf_counter() - self._start_time
            if self.on_complete is not None:
                self.on_complete(self.name, self._elapsed_seconds)

    def __call__(self, func: F) -> F:
        """Use timed as a decorator."""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with timed(self.name, self.on_complete):
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]
