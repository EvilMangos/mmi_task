"""Tests for TelegramSettings."""

import pytest
from pydantic import ValidationError

from config.telegram import TelegramSettings


class TestTelegramSettings:
    """Tests for TelegramSettings validation."""

    def test_valid_settings(self) -> None:
        """Valid bot_token and chat_id are accepted."""
        settings = TelegramSettings(
            bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            chat_id="-1001234567890",
        )
        assert settings.bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert settings.chat_id == "-1001234567890"

    def test_strips_whitespace_from_bot_token(self) -> None:
        """Whitespace is stripped from bot_token."""
        settings = TelegramSettings(
            bot_token="  my_token  ",
            chat_id="123",
        )
        assert settings.bot_token == "my_token"

    def test_strips_whitespace_from_chat_id(self) -> None:
        """Whitespace is stripped from chat_id."""
        settings = TelegramSettings(
            bot_token="token",
            chat_id="  -1001234567890  ",
        )
        assert settings.chat_id == "-1001234567890"

    def test_empty_bot_token_raises_error(self) -> None:
        """Empty bot_token raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramSettings(bot_token="", chat_id="123")
        assert "bot_token must not be empty" in str(exc_info.value)

    def test_whitespace_only_bot_token_raises_error(self) -> None:
        """Whitespace-only bot_token raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramSettings(bot_token="   ", chat_id="123")
        assert "bot_token must not be empty" in str(exc_info.value)

    def test_empty_chat_id_raises_error(self) -> None:
        """Empty chat_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramSettings(bot_token="token", chat_id="")
        assert "chat_id must not be empty" in str(exc_info.value)

    def test_whitespace_only_chat_id_raises_error(self) -> None:
        """Whitespace-only chat_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramSettings(bot_token="token", chat_id="  \t  ")
        assert "chat_id must not be empty" in str(exc_info.value)

    def test_settings_are_immutable(self) -> None:
        """Settings object is frozen and cannot be modified."""
        settings = TelegramSettings(bot_token="token", chat_id="123")
        with pytest.raises(ValidationError):
            setattr(settings, "bot_token", "new_token")
