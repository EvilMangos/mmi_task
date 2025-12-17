# config

Typed configuration settings for crypto orderbook alerts using Pydantic v2.

## Purpose

Provides validated configuration management. Settings are loaded from environment variables with sensible defaults and
strict type validation.

## Installation

```bash
pip install -e "packages/config[dev]"
```

## Usage

```python
from config import load_settings, Settings

settings = load_settings()

# Access sub-settings
print(settings.telegram.bot_token)
print(settings.binance.symbols)
print(settings.alerting.imbalance_threshold)
print(settings.logging.log_level)
```

## Exports

| Export               | Description                                 |
|----------------------|---------------------------------------------|
| `Settings`           | Root settings model                         |
| `load_settings()`    | Load and validate settings from environment |
| `TelegramSettings`   | Telegram bot configuration                  |
| `BinanceSettings`    | Binance connection settings                 |
| `AlertingSettings`   | Alert thresholds and cooldowns              |
| `LoggingSettings`    | Log level configuration                     |
| `LogLevel`           | Enum of valid log levels                    |
| `ConfigurationError` | Raised on invalid configuration             |

## Environment Variables

### Required

| Variable              | Description                                       |
|-----------------------|---------------------------------------------------|
| `TELEGRAM_BOT_TOKEN`  | Telegram bot token                                |
| `TELEGRAM_CHAT_ID`    | Destination chat/channel ID                       |
| `SYMBOLS`             | Comma-separated symbols (e.g., `BTCUSDT,DOTUSDT`) |
| `IMBALANCE_THRESHOLD` | Alert threshold float (e.g., `0.35`)              |

### Optional

| Variable                 | Default     | Description                  |
|--------------------------|-------------|------------------------------|
| `TOP_N_LEVELS`           | `10`        | Order book levels to analyze |
| `ALERT_COOLDOWN_SECONDS` | `30`        | Per-symbol cooldown          |
| `BINANCE_WS_URL`         | Official WS | WebSocket URL override       |
| `LOG_LEVEL`              | `INFO`      | Logging level                |
| `HEALTH_PORT`            | `8080`      | Health endpoint port         |

## Testing

```bash
cd packages/config && pytest
```

### Test Fixtures

The package provides test fixtures in `conftest.py`:

```python
from config.conftest import patched_env, make_valid_env

# Test with valid environment
with patched_env() as env:
    settings = Settings(_env_file=None)

# Test with custom overrides
with patched_env(overrides={"LOG_LEVEL": "DEBUG"}):
    settings = Settings(_env_file=None)

# Test missing required variable
with patched_env(remove=["TELEGRAM_BOT_TOKEN"]):
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
```
