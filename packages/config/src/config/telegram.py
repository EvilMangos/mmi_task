"""Telegram notification settings."""

from pydantic import BaseModel, field_validator


class TelegramSettings(BaseModel, frozen=True):
    """Settings for Telegram bot notifications.

    Attributes:
        bot_token: Telegram bot API token (from BotFather).
        chat_id: Target chat or channel ID for sending alerts.
    """

    bot_token: str
    chat_id: str

    @field_validator("bot_token")
    @classmethod
    def bot_token_not_empty(cls, v: str) -> str:
        """Validate that bot_token is not empty or whitespace-only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("bot_token must not be empty")
        return stripped

    @field_validator("chat_id")
    @classmethod
    def chat_id_not_empty(cls, v: str) -> str:
        """Validate that chat_id is not empty or whitespace-only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("chat_id must not be empty")
        return stripped
