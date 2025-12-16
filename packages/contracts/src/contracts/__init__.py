"""Contracts package - shared protocols and interfaces.

This package provides common interfaces used across the monorepo
to enable loose coupling between packages. Only protocols (interfaces)
belong here - no concrete implementations.
"""

from contracts.clock import Clock

__all__ = [
    "Clock",
]
