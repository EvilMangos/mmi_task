"""Telegram notification settings."""

from pydantic import BaseModel, ConfigDict, field_validator


def _validate_non_empty_string(v: str, field_name: str) -> str:
    """Validate and strip a string field, raising ValueError if empty."""
    stripped = v.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    return stripped


class TelegramSettings(BaseModel):
    """Settings for Telegram bot notifications.

    Attributes:
        bot_token: Telegram bot API token (from BotFather).
        chat_id: Target chat or channel ID for sending alerts.
    """

    model_config = ConfigDict(frozen=True)

    bot_token: str
    chat_id: str

    @field_validator("bot_token")
    @classmethod
    def bot_token_not_empty(cls, v: str) -> str:
        """Validate that bot_token is not empty or whitespace-only."""
        return _validate_non_empty_string(v, "bot_token")

    @field_validator("chat_id")
    @classmethod
    def chat_id_not_empty(cls, v: str) -> str:
        """Validate that chat_id is not empty or whitespace-only."""
        return _validate_non_empty_string(v, "chat_id")
