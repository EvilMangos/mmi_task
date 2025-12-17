# notifier-telegram

Telegram Bot API client for sending imbalance alerts.

## Purpose

Implements the `Notifier` protocol from `contracts` to send formatted alert messages via Telegram.

## Installation

```bash
pip install -e "packages/notifier_telegram[dev]"
```

## Dependencies

- `contracts` - Notifier protocol
- `aiohttp` - Async HTTP client

## Exports

```python
from notifier_telegram import (
    TelegramNotifier,
    AlertPayload,
    format_alert_message,
    NotifierError,
    TransientNotifierError,
    PermanentNotifierError,
)
```

### TelegramNotifier

Async context manager implementing the `Notifier` protocol:

```python
from notifier_telegram import TelegramNotifier, AlertPayload

async with TelegramNotifier(
        bot_token="123:abc...",
        chat_id="-1001234567890",
) as notifier:
    alert = AlertPayload(
        symbol="BTCUSDT",
        ratio=0.42,
        bid_volume=150.0,
        ask_volume=100.0,
        timestamp=1704067200.0,
        threshold=0.35,
    )
    await notifier.send_alert(alert)
```

### AlertPayload

Dataclass containing alert data:

```python
from notifier_telegram import AlertPayload

alert = AlertPayload(
    symbol="BTCUSDT",
    ratio=0.42,
    bid_volume=150.0,
    ask_volume=100.0,
    timestamp=1704067200.0,
    threshold=0.35,
)
```

### Message Formatting

```python
from notifier_telegram import format_alert_message, AlertPayload

alert = AlertPayload(...)
message = format_alert_message(alert)
# Returns formatted Telegram message with emoji indicators
```

## Error Handling

```python
from notifier_telegram import TransientNotifierError, PermanentNotifierError

try:
    await notifier.send_alert(alert)
except TransientNotifierError:
    # Retry later (network timeout, rate limit, 5xx)
    pass
except PermanentNotifierError:
    # Don't retry (invalid token, 4xx)
    pass
```

## Testing

```bash
cd packages/notifier_telegram && pytest
```

### Test Utilities

The `testing` subpackage provides factories:

```python
from notifier_telegram.testing import PayloadFactory

alert = PayloadFactory.create(symbol="BTCUSDT", ratio=0.5)
```

## Configuration

Via environment variables (see `config` package):

| Variable             | Description               |
|----------------------|---------------------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID`   | Target chat/channel ID    |
