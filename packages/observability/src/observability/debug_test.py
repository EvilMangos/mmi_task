"""Tests for debug toggle."""

from __future__ import annotations

import pytest


class TestIsDebugEnabled:
    """Tests for is_debug_enabled function."""

    def test_is_debug_enabled_returns_false_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When DEBUG env var is not set, returns False."""
        from observability.debug import is_debug_enabled

        monkeypatch.delenv("DEBUG", raising=False)

        result = is_debug_enabled()

        assert result is False

    def test_is_debug_enabled_returns_true_for_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When DEBUG is '1', returns True."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "1")

        result = is_debug_enabled()

        assert result is True

    def test_is_debug_enabled_returns_true_for_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When DEBUG is 'true', returns True."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "true")

        result = is_debug_enabled()

        assert result is True

    def test_is_debug_enabled_returns_true_for_yes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When DEBUG is 'yes', returns True."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "yes")

        result = is_debug_enabled()

        assert result is True

    def test_is_debug_enabled_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DEBUG value check is case-insensitive."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "TRUE")
        assert is_debug_enabled() is True

        monkeypatch.setenv("DEBUG", "True")
        assert is_debug_enabled() is True

        monkeypatch.setenv("DEBUG", "YES")
        assert is_debug_enabled() is True

        monkeypatch.setenv("DEBUG", "Yes")
        assert is_debug_enabled() is True

    def test_is_debug_enabled_returns_false_for_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When DEBUG is '0', returns False."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "0")

        result = is_debug_enabled()

        assert result is False

    def test_is_debug_enabled_returns_false_for_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When DEBUG is 'false', returns False."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "false")

        result = is_debug_enabled()

        assert result is False

    def test_is_debug_enabled_returns_false_for_random_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When DEBUG is a random non-truthy string, returns False."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "maybe")

        result = is_debug_enabled()

        assert result is False

    def test_is_debug_enabled_returns_false_for_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When DEBUG is empty string, returns False."""
        from observability.debug import is_debug_enabled

        monkeypatch.setenv("DEBUG", "")

        result = is_debug_enabled()

        assert result is False
