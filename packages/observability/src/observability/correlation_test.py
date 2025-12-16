"""Tests for correlation ID context management."""

from __future__ import annotations

import asyncio

import pytest


class TestGetCorrelationId:
    """Tests for get_correlation_id function."""

    def test_get_correlation_id_returns_none_when_not_set(self) -> None:
        """When no correlation ID has been set, get_correlation_id returns None."""
        from observability.correlation import get_correlation_id

        result = get_correlation_id()

        assert result is None


class TestSetAndGetCorrelationId:
    """Tests for set_correlation_id and get_correlation_id interaction."""

    def test_set_and_get_correlation_id(self) -> None:
        """After setting a correlation ID, get_correlation_id returns that value."""
        from observability.correlation import (
            get_correlation_id,
            reset_correlation_id,
            set_correlation_id,
        )

        token = set_correlation_id("test-correlation-123")
        try:
            result = get_correlation_id()
            assert result == "test-correlation-123"
        finally:
            reset_correlation_id(token)


class TestResetCorrelationId:
    """Tests for reset_correlation_id function."""

    def test_reset_correlation_id_restores_previous(self) -> None:
        """Resetting with a token restores the previous correlation ID value."""
        from observability.correlation import (
            get_correlation_id,
            reset_correlation_id,
            set_correlation_id,
        )

        # Set initial value
        token1 = set_correlation_id("first-id")
        try:
            # Set second value
            token2 = set_correlation_id("second-id")
            assert get_correlation_id() == "second-id"

            # Reset to first value
            reset_correlation_id(token2)
            assert get_correlation_id() == "first-id"
        finally:
            reset_correlation_id(token1)

        # After all resets, should be None
        assert get_correlation_id() is None


class TestCorrelationContext:
    """Tests for correlation_context context manager."""

    def test_correlation_context_sets_and_resets(self) -> None:
        """Context manager sets correlation ID on enter and resets on exit."""
        from observability.correlation import correlation_context, get_correlation_id

        assert get_correlation_id() is None

        with correlation_context("context-id-456"):
            assert get_correlation_id() == "context-id-456"

        assert get_correlation_id() is None

    def test_correlation_context_generates_id_when_none(self) -> None:
        """When called with None, context manager generates a new correlation ID."""
        from observability.correlation import correlation_context, get_correlation_id

        with correlation_context(None):
            cid = get_correlation_id()
            assert cid is not None
            assert isinstance(cid, str)
            assert len(cid) > 0

        assert get_correlation_id() is None

    def test_correlation_context_preserves_existing_on_exit(self) -> None:
        """Nested contexts properly restore outer correlation IDs."""
        from observability.correlation import correlation_context, get_correlation_id

        with correlation_context("outer-id"):
            assert get_correlation_id() == "outer-id"

            with correlation_context("inner-id"):
                assert get_correlation_id() == "inner-id"

            # After inner context exits, outer ID is restored
            assert get_correlation_id() == "outer-id"

        assert get_correlation_id() is None


class TestCorrelationIdAsyncIsolation:
    """Tests for async task isolation of correlation IDs."""

    @pytest.mark.asyncio
    async def test_correlation_id_isolated_across_async_tasks(self) -> None:
        """Each async task has its own correlation ID context."""
        from observability.correlation import correlation_context, get_correlation_id

        results: dict[str, str | None] = {}

        async def task_with_correlation(task_name: str, cid: str) -> None:
            with correlation_context(cid):
                # Small delay to allow task interleaving
                await asyncio.sleep(0.01)
                results[task_name] = get_correlation_id()

        # Run multiple tasks concurrently with different correlation IDs
        await asyncio.gather(
            task_with_correlation("task1", "id-for-task1"),
            task_with_correlation("task2", "id-for-task2"),
            task_with_correlation("task3", "id-for-task3"),
        )

        # Each task should have captured its own correlation ID
        assert results["task1"] == "id-for-task1"
        assert results["task2"] == "id-for-task2"
        assert results["task3"] == "id-for-task3"
