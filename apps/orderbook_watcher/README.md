# orderbook-watcher

Deployable async service for monitoring crypto order book imbalances.

## Purpose

This is the main runtime application that:

1. Connects to Binance WebSocket for real-time order book data
2. Computes imbalance ratios for configured symbols
3. Sends Telegram alerts when thresholds are exceeded
4. Handles graceful shutdown and reconnection

## Installation

```bash
pip install -e "apps/orderbook_watcher[dev]"
```

## Dependencies

- `contracts` - Shared protocols
- `config` - Settings management
- `domain-orderbook` - Order book types
- `domain-imbalance` - Ratio calculation
- `signal-engine` - Threshold evaluation
- `connector-binance` - Binance WebSocket client
- `notifier-telegram` - Telegram notifications
- `observability` - Logging and metrics

## Running

### Direct Execution

```bash
# As module
python -m orderbook_watcher

# Via console entrypoint
orderbook-watcher
```

### Docker

```bash
# From project root
docker compose up --build
```

### Systemd

A systemd unit file is provided at `orderbook_watcher.service` for production deployment.

## Exports

```python
from orderbook_watcher import main, Watcher, RealClock, HealthServer
```

### Watcher

Core processing component:

```python
from orderbook_watcher import Watcher

watcher = Watcher(
    evaluator=signal_evaluator,
    notifier=telegram_notifier,
    threshold=0.35,
    top_n_levels=10,
)

# Process snapshots from feed
async for snapshot in feed.snapshots():
    await watcher.process_snapshot(snapshot)
```

### RealClock

Production `Clock` implementation using UTC:

```python
from orderbook_watcher import RealClock

clock = RealClock()
now = clock.now()  # Returns current UTC datetime
```

### HealthServer

Optional HTTP health endpoint:

```python
from orderbook_watcher import HealthServer

async with HealthServer(port=8080) as server:
    # GET /health returns 200 OK
    ...
```

## Configuration

Environment variables (via `config` package):

| Variable                 | Required | Default | Description          |
|--------------------------|----------|---------|----------------------|
| `TELEGRAM_BOT_TOKEN`     | Yes      | -       | Telegram bot token   |
| `TELEGRAM_CHAT_ID`       | Yes      | -       | Target chat ID       |
| `SYMBOLS`                | Yes      | -       | Symbols to watch     |
| `IMBALANCE_THRESHOLD`    | Yes      | -       | Alert threshold      |
| `TOP_N_LEVELS`           | No       | `10`    | Levels to analyze    |
| `ALERT_COOLDOWN_SECONDS` | No       | `30`    | Cooldown per symbol  |
| `LOG_LEVEL`              | No       | `INFO`  | Logging level        |
| `HEALTH_PORT`            | No       | `8080`  | Health endpoint port |

## Signal Handling

The service handles graceful shutdown on:

- `SIGINT` (Ctrl+C)
- `SIGTERM` (container stop)

## Testing

```bash
cd apps/orderbook_watcher && pytest
```

### Test Fixtures

The app provides specialized fixtures in `conftest.py`:

```python
def test_with_fixtures(fake_clock, fake_notifier):
    # fake_clock starts at 2025-01-15 12:00:00 UTC
    # fake_notifier uses AlertPayload protocol
    ...
```

## Architecture

```
┌────────────────┐
│     main()     │  Entry point, signal handling
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    Watcher     │  Coordinates processing
└───────┬────────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
BinanceFeed  TelegramNotifier
(connector)  (notifier)
```
