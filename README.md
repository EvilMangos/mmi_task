# Crypto Order Book Imbalance Watcher

A real-time crypto order book imbalance monitoring system that connects to Binance, calculates bid/ask volume
imbalances, and sends Telegram alerts when thresholds are exceeded.

## Overview

This system:

1. Streams real-time order book data from Binance for configured symbols (e.g., BTCUSDT, DOTUSDT, SOLUSDT)
2. Computes bid/ask volumes for the top N levels (default: 10)
3. Calculates the imbalance ratio: `(Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)`
4. Sends Telegram alerts when the ratio exceeds a configurable threshold
5. Applies cooldown/dedupe logic to avoid alert spam

## Quick Start

### Prerequisites

- Python 3.11+
- A Telegram bot token and chat ID
- Internet access for Binance WebSocket connection

### Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   ./scripts/reinstall_packages.sh
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram credentials
   ```

4. **Run the watcher:**
   ```bash
   python -m orderbook_watcher
   # or
   orderbook-watcher
   ```

### Docker

```bash
docker compose up --build
```

## Configuration

| Variable                 | Required | Default     | Description                                       |
|--------------------------|----------|-------------|---------------------------------------------------|
| `TELEGRAM_BOT_TOKEN`     | Yes      | -           | Telegram bot token                                |
| `TELEGRAM_CHAT_ID`       | Yes      | -           | Destination chat/channel ID                       |
| `SYMBOLS`                | Yes      | -           | Comma-separated symbols (e.g., `BTCUSDT,DOTUSDT`) |
| `IMBALANCE_THRESHOLD`    | Yes      | -           | Alert threshold (e.g., `0.35`)                    |
| `TOP_N_LEVELS`           | No       | `10`        | Number of order book levels to analyze            |
| `ALERT_COOLDOWN_SECONDS` | No       | `30`        | Per-symbol cooldown to avoid spam                 |
| `BINANCE_WS_URL`         | No       | Official WS | Optional WebSocket URL override                   |
| `LOG_LEVEL`              | No       | `INFO`      | Logging level                                     |
| `HEALTH_PORT`            | No       | `8080`      | Health endpoint port                              |

## Project Structure

```
.
├── apps/
│   └── orderbook_watcher/     # Deployable async service
├── packages/
│   ├── contracts/             # Shared protocols (Clock, Notifier)
│   ├── config/                # Typed settings (Pydantic)
│   ├── domain_orderbook/      # Order book types and helpers
│   ├── domain_imbalance/      # Imbalance ratio calculation
│   ├── signal_engine/         # Threshold evaluation and cooldown
│   ├── connector_binance/     # Binance WebSocket client
│   ├── notifier_telegram/     # Telegram Bot API client
│   ├── observability/         # Logging, metrics, tracing
│   └── testkit/               # Shared test fixtures and fakes
└── scripts/                   # Development scripts
```

## Development

### Running Tests

```bash
# All tests
pytest

# Single package
cd packages/domain_imbalance && pytest

# Verbose output
pytest -v
```

### Code Quality

```bash
ruff format .
ruff check .
mypy .
```

### Installing Packages

Individual packages can be installed in editable mode:

```bash
pip install -e "packages/contracts[dev]"
pip install -e "packages/config[dev]"
# ... etc
```

Or use the reinstall script:

```bash
./scripts/reinstall_packages.sh
```

## Data Flow

```
Binance WebSocket
       │
       ▼
┌─────────────────┐
│ connector_binance│ ──► normalized OrderBookSnapshot
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ domain_orderbook │ ──► top N levels extraction
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ domain_imbalance │ ──► sum volumes + compute ratio
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  signal_engine   │ ──► threshold check + cooldown
└─────────────────┘
       │
       ▼
┌─────────────────┐
│notifier_telegram │ ──► send Telegram alert
└─────────────────┘
```

## License

This project is proprietary software.
