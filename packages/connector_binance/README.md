# connector-binance

Binance WebSocket client that emits normalized order book events.

## Purpose

Connects to Binance public market data WebSocket and streams real-time order book updates as normalized
`OrderBookSnapshot` objects.

## Installation

```bash
pip install -e "packages/connector_binance[dev]"
```

## Dependencies

- `domain-orderbook` - Snapshot types
- `config` - Binance settings
- `observability` - Logging
- `websockets` - WebSocket client

## Exports

```python
from connector_binance import BinanceFeed, ExponentialBackoff, ParseError, parse_depth_message
```

### BinanceFeed

Async context manager for streaming order book snapshots:

```python
from connector_binance import BinanceFeed
from config import BinanceSettings

settings = BinanceSettings(
    symbols=["BTCUSDT", "DOTUSDT"],
    top_n_levels=10,
)

async with BinanceFeed(settings) as feed:
    async for snapshot in feed.snapshots():
        print(f"{snapshot.symbol}: {len(snapshot.bids)} bids, {len(snapshot.asks)} asks")
```

### ExponentialBackoff

Backoff strategy for reconnection:

```python
from connector_binance import ExponentialBackoff

backoff = ExponentialBackoff(base=1.0, max_delay=60.0)
delay = backoff.next_delay()  # 1.0, 2.0, 4.0, 8.0, ... up to 60.0
backoff.reset()  # Reset after successful connection
```

### Message Parsing

```python
from connector_binance import parse_depth_message, ParseError

try:
    snapshot = parse_depth_message(raw_message)
except ParseError as e:
    print(f"Invalid message: {e}")
```

## Features

- Multi-symbol subscription in single connection
- Automatic reconnection with exponential backoff
- Graceful shutdown via context manager
- Normalized output as `OrderBookSnapshot`

## Testing

```bash
cd packages/connector_binance && pytest
```

### Test Utilities

The `testing` subpackage provides message builders:

```python
from connector_binance.testing import MessageBuilder

msg = MessageBuilder.depth_update(
    symbol="BTCUSDT",
    bids=[("45000.00", "1.5")],
    asks=[("45001.00", "1.2")],
)
```

## Configuration

Via environment variables (see `config` package):

| Variable         | Description              |
|------------------|--------------------------|
| `SYMBOLS`        | Comma-separated symbols  |
| `TOP_N_LEVELS`   | Levels per side          |
| `BINANCE_WS_URL` | Optional WS URL override |
