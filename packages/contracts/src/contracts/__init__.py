"""Contracts package - shared protocols and interfaces.

This package provides common interfaces used across the monorepo
to enable loose coupling between packages. Only protocols (interfaces)
belong here - no concrete implementations.
"""

from contracts.clock import Clock
from contracts.notifier import (
    AlertPayload,
    Notifier,
    NotifierError,
    PermanentNotifierError,
    TransientNotifierError,
)

__all__ = [
    "AlertPayload",
    "Clock",
    "Notifier",
    "NotifierError",
    "PermanentNotifierError",
    "TransientNotifierError",
]
