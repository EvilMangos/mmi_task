"""Correlation ID management using context variables."""

import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context.

    Returns None if no correlation ID has been set.
    """
    return _correlation_id.get()


def set_correlation_id(cid: str) -> Token[str | None]:
    """Set the correlation ID in the current context.

    Args:
        cid: The correlation ID to set.

    Returns:
        A token that can be used to reset the correlation ID.
    """
    return _correlation_id.set(cid)


def reset_correlation_id(token: Token[str | None]) -> None:
    """Reset the correlation ID to its previous value.

    Args:
        token: The token returned by set_correlation_id.
    """
    _correlation_id.reset(token)


@contextmanager
def correlation_context(cid: str | None = None) -> Iterator[str]:
    """Context manager for setting a correlation ID.

    If cid is None, a new UUID will be generated.

    Args:
        cid: Optional correlation ID. If None, generates a UUID.

    Yields:
        The correlation ID being used.
    """
    if cid is None:
        cid = str(uuid.uuid4())
    token = set_correlation_id(cid)
    try:
        yield cid
    finally:
        reset_correlation_id(token)
