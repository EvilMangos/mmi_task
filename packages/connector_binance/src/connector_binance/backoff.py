"""Exponential backoff implementation for reconnection delays."""


class ExponentialBackoff:
    """Calculates exponential backoff delays for reconnection attempts.

    The delay starts at base_delay and multiplies by the multiplier on each
    subsequent call to next_delay(). The delay is capped at max_delay.

    Attributes:
        base_delay: Initial delay in seconds.
        multiplier: Factor to multiply delay by on each failure.
        max_delay: Maximum delay cap in seconds.
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        multiplier: float = 2.0,
        max_delay: float = 60.0,
    ) -> None:
        """Initialize the backoff calculator.

        Args:
            base_delay: Initial delay in seconds (default: 1.0).
            multiplier: Factor to multiply delay by on each failure (default: 2.0).
            max_delay: Maximum delay cap in seconds (default: 60.0).
        """
        self._base_delay = base_delay
        self._multiplier = multiplier
        self._max_delay = max_delay
        self._current_delay = base_delay

    def next_delay(self) -> float:
        """Get the next delay and advance the backoff state.

        Returns:
            The next delay in seconds, capped at max_delay.
        """
        # Apply cap to current delay
        delay = min(self._current_delay, self._max_delay)
        # Advance state for next call
        self._current_delay *= self._multiplier
        return delay

    def reset(self) -> None:
        """Reset the backoff state to the initial delay."""
        self._current_delay = self._base_delay
