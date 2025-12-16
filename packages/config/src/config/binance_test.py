"""Tests for BinanceSettings."""

import pytest
from pydantic import ValidationError

from config.binance import (
    DEFAULT_BINANCE_WS_URL,
    DEFAULT_TOP_N_LEVELS,
    MAX_TOP_N_LEVELS,
    MIN_TOP_N_LEVELS,
    BinanceSettings,
)


class TestBinanceSettings:
    """Tests for BinanceSettings validation."""

    def test_valid_settings_with_defaults(self) -> None:
        """Valid symbols with default values are accepted."""
        settings = BinanceSettings(symbols="BTCUSDT")
        assert settings.symbols == ["BTCUSDT"]
        assert settings.ws_url == DEFAULT_BINANCE_WS_URL
        assert settings.top_n_levels == DEFAULT_TOP_N_LEVELS

    def test_parses_comma_separated_symbols(self) -> None:
        """Comma-separated symbols string is parsed into list."""
        settings = BinanceSettings(symbols="BTCUSDT,DOTUSDT,SOLUSDT")
        assert settings.symbols == ["BTCUSDT", "DOTUSDT", "SOLUSDT"]

    def test_normalizes_symbols_to_uppercase(self) -> None:
        """Symbols are normalized to uppercase."""
        settings = BinanceSettings(symbols="btcusdt,DotUsdt,solUSDT")
        assert settings.symbols == ["BTCUSDT", "DOTUSDT", "SOLUSDT"]

    def test_strips_whitespace_from_symbols(self) -> None:
        """Whitespace is stripped from symbols."""
        settings = BinanceSettings(symbols="  BTCUSDT , DOTUSDT  ,  SOLUSDT  ")
        assert settings.symbols == ["BTCUSDT", "DOTUSDT", "SOLUSDT"]

    def test_handles_extra_commas(self) -> None:
        """Extra commas resulting in empty entries are ignored."""
        settings = BinanceSettings(symbols="BTCUSDT,,DOTUSDT,")
        assert settings.symbols == ["BTCUSDT", "DOTUSDT"]

    def test_accepts_symbols_as_list(self) -> None:
        """Symbols can also be provided as a list directly."""
        settings = BinanceSettings(symbols=["btcusdt", "dotusdt"])
        assert settings.symbols == ["BTCUSDT", "DOTUSDT"]

    @pytest.mark.parametrize(
        "symbols",
        [
            pytest.param("", id="empty_string"),
            pytest.param("   ,  ,  ", id="whitespace_only"),
            pytest.param([], id="empty_list"),
        ],
    )
    def test_empty_symbols_raises_error(self, symbols: str | list[str]) -> None:
        """Empty or whitespace-only symbols raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BinanceSettings(symbols=symbols)
        assert "symbols must contain at least one item" in str(exc_info.value)

    def test_valid_wss_url(self) -> None:
        """WSS URL is accepted."""
        settings = BinanceSettings(
            symbols="BTCUSDT",
            ws_url="wss://custom.binance.com/ws",
        )
        assert settings.ws_url == "wss://custom.binance.com/ws"

    def test_valid_ws_url(self) -> None:
        """WS (non-secure) URL is accepted."""
        settings = BinanceSettings(
            symbols="BTCUSDT",
            ws_url="ws://localhost:8080/ws",
        )
        assert settings.ws_url == "ws://localhost:8080/ws"

    def test_strips_whitespace_from_ws_url(self) -> None:
        """Whitespace is stripped from ws_url."""
        settings = BinanceSettings(
            symbols="BTCUSDT",
            ws_url="  wss://stream.binance.com/ws  ",
        )
        assert settings.ws_url == "wss://stream.binance.com/ws"

    @pytest.mark.parametrize(
        "invalid_url",
        [
            pytest.param("https://binance.com", id="https_protocol"),
            pytest.param("http://binance.com", id="http_protocol"),
        ],
    )
    def test_invalid_ws_url_protocol_raises_error(self, invalid_url: str) -> None:
        """Non-websocket URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BinanceSettings(symbols="BTCUSDT", ws_url=invalid_url)
        assert "ws_url must start with ws:// or wss://" in str(exc_info.value)

    def test_top_n_levels_minimum_boundary(self) -> None:
        """Minimum valid top_n_levels (1) is accepted."""
        settings = BinanceSettings(symbols="BTCUSDT", top_n_levels=MIN_TOP_N_LEVELS)
        assert settings.top_n_levels == MIN_TOP_N_LEVELS

    def test_top_n_levels_maximum_boundary(self) -> None:
        """Maximum valid top_n_levels (100) is accepted."""
        settings = BinanceSettings(symbols="BTCUSDT", top_n_levels=MAX_TOP_N_LEVELS)
        assert settings.top_n_levels == MAX_TOP_N_LEVELS

    @pytest.mark.parametrize(
        "invalid_value",
        [
            pytest.param(0, id="below_minimum"),
            pytest.param(101, id="above_maximum"),
            pytest.param(-5, id="negative"),
        ],
    )
    def test_invalid_top_n_levels_raises_error(self, invalid_value: int) -> None:
        """Invalid top_n_levels values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BinanceSettings(symbols="BTCUSDT", top_n_levels=invalid_value)
        assert "top_n_levels must be between" in str(exc_info.value)

    def test_settings_are_immutable(self) -> None:
        """Settings object is frozen and cannot be modified."""
        settings = BinanceSettings(symbols="BTCUSDT")
        with pytest.raises(ValidationError):
            settings.symbols = ["ETHUSDT"]  # type: ignore[misc]
