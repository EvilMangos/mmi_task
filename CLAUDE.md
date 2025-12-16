This file provides guidance to Claude Code (claude.ai/code) when working with code
in this repository.

---

## Repository Overview

This is a **Python monorepo** for a real-time **crypto order book imbalance watcher**.

The task behind the project:
Connect to Binance to get real-time order book data for tickers like BTC/USDT,DOT/USDT,SOL/USDT
- Calculate the volume ratio on the buyers and sellers side for the 10 best bids and 10 best asks using the formula
Imbalance Ratio = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)
- Set up a telegram alert using the telegram bot when Imbalance Ratio > X. X must be set in the configuration.

Core behavior:

1) Connect to **Binance** (public market data) to stream real-time order book updates for configured symbols
   (e.g., `BTCUSDT`, `DOTUSDT`, `SOLUSDT`).
2) For each symbol, compute bid/ask volumes for the **top N levels** (default: 10 bids + 10 asks).
3) Compute:

   Imbalance Ratio = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)

4) Send a **Telegram alert** when `Imbalance Ratio > X` where `X` is configurable.
5) Apply alert **dedupe/cooldown** to avoid spamming.

Non-goals:

- No trading / order placement. This is read-only market data + notifications.
- No "always-on" infra assumptions: treat runtime as local/dev unless explicitly stated.

---

## Development Commands

### Environment Setup

Always install dependencies inside a virtual environment.
Assume Python **3.11+** (3.10+ acceptable if required).

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
````

### Installing Dependencies

This monorepo uses editable installs for local packages.

Option A (recommended): install everything in one go (if script exists):

```bash
./scripts/reinstall_packages.sh
```

Option B: install manually (example):

```bash
pip install -U pip
pip install -e "packages/config[dev]"
pip install -e "packages/domain_orderbook[dev]"
pip install -e "packages/domain_imbalance[dev]"
pip install -e "packages/observability[dev]"
pip install -e "packages/signal_engine[dev]"
pip install -e "packages/testkit[dev]"
pip install -e "packages/connector_binance[dev]"
pip install -e "packages/notifier_telegram[dev]"
pip install -e "apps/orderbook_watcher[dev]"
```

### Running the Watcher

Run the deployable app:

```bash
python -m orderbook_watcher
```

Or via the console entrypoint (if installed):

```bash
orderbook-watcher
```

### Testing

Prefer the smallest scope that validates your change.

```bash
# Run all tests
pytest

# Run tests for a single package/app (examples)
cd packages/domain_imbalance && pytest
cd packages/signal_engine && pytest
cd apps/orderbook_watcher && pytest

# Run a single test file
pytest path/to/test_file_test.py

# Verbose output
pytest -v
```

### Code Quality

```bash
ruff format .
ruff check .
mypy .
```

---

## Architecture

### Monorepo Structure (expected)

```text
crypto-orderbook-alerts/
├── apps/
│   └── orderbook_watcher/                 # deployable async service
│       ├── Dockerfile                     # container image
│       ├── orderbook_watcher.service      # systemd unit for deployment
│       └── src/orderbook_watcher/
│           ├── __main__.py                # module runner (python -m orderbook_watcher)
│           ├── main.py                    # bootstrap + graceful shutdown
│           ├── watcher.py                 # wiring: stream -> compute -> evaluate -> notify
│           ├── real_clock.py              # production Clock implementation (UTC)
│           └── health.py                  # optional /health and /metrics endpoints
├── scripts/
│   ├── lint_and_format.sh                 # run ruff format + ruff check
│   └── reinstall_packages.sh              # uninstall and reinstall all local packages
└── packages/
    ├── config/                            # typed settings (threshold X, symbols, telegram creds, etc.)
    ├── domain_orderbook/                  # pure orderbook types + "top N levels" helpers
    ├── domain_imbalance/                  # pure math: volume sums + imbalance ratio
    ├── signal_engine/                     # threshold evaluation + cooldown/dedupe logic
    ├── connector_binance/                 # Binance websocket + snapshot sync; emits normalized snapshots
    ├── notifier_telegram/                 # Telegram Bot API client + message formatting
    ├── observability/                     # logging/metrics helpers
    └── testkit/                           # optional shared fixtures/fakes (tests still live next to code)
```

### Boundary Rules (very important)

* `domain-*` packages are **pure**: no network calls, no environment reads, no time access.
* `connector-binance` is the only package that knows Binance protocol details.
* `notifier-telegram` is the only package that knows Telegram API details.
* `apps/orderbook-watcher` wires everything together and owns:

    * `asyncio` event loop
    * lifecycle + shutdown
    * composition and configuration loading

### Data Flow

For each symbol:

`connector-binance` -> normalized `OrderBookSnapshot` ->
`domain-orderbook` (top N) ->
`domain-imbalance` (sum + ratio) ->
`signal-engine` (ratio > X + cooldown/dedupe) ->
`notifier-telegram` (send alert)

---

## Design Rules

### Code Style

* Max line length: **100**
* Use **type hints** everywhere in production code.
* Avoid `Any` unless truly required.
* Prefer self-documenting code; keep comments minimal and targeted.
* Imports at the top; avoid local imports unless needed to break heavy deps / cycles.

### Single Responsibility

* Each file should define a **single top-level element** (class, protocol, “main function”, etc.).
* Small private helpers (`_helper`) are fine inside that file.
* If a file grows “multi-purpose”, split it.

### Interfaces / Dependency Inversion

Prefer `Protocol`-based interfaces at boundaries:

* `OrderBookFeed` (Binance adapter implements it)
* `Notifier` (Telegram adapter implements it)
* `Clock` (injectable time source for deterministic cooldown tests)

Do not instantiate heavy dependencies (websocket clients, HTTP sessions) in pure domain code.

### Async Rules

* Use `asyncio` consistently. Avoid mixing sync and async in the same boundary.
* Adapters may create internal tasks, but must expose explicit `start()` / `stop()` or `connect()` / `disconnect()`.
* Always handle reconnect/backoff in adapters; never crash the whole app on transient network errors.

---

## Testing Guidelines

### Where Tests Live

* Test files are named `*_test.py`
* Tests live **near the code they test** (inside each package/app).
* `packages/testkit` is optional and only for shared fixtures/fakes.

### What to Test (value-first)

* `domain-imbalance`: math correctness, edge cases (zero volumes, rounding/float behavior).
* `signal-engine`: threshold logic, cooldown, dedupe, hysteresis (if used).
* `connector-binance`: protocol correctness via mocked websocket frames; resync behavior.
* `notifier-telegram`: formatting + minimal HTTP interaction (mock requests).
* `orderbook-watcher`: wiring integration test with faked feed + fake notifier.

### What *Not* to Test

Avoid:

* pure implementation details (private helpers, internal call order)
* trivial getters/setters
* “constructor wiring” tests that only assert attribute assignment
* brittle “call choreography” expectations

Constructor tests are only worth it if `__init__` validates input, normalizes values, or establishes
invariants relied on by public behavior.

### External Systems Isolation

Use fakes/mocks for:

* Binance websocket
* Telegram HTTP
* time (clock)
* randomness (if any)

Tests should be deterministic and cheap.

### Testkit Utilities

The `packages/testkit` package provides shared testing utilities:

* `FakeClock` - injectable time source for deterministic cooldown tests
* `FakeNotifier` - records notification calls for inspection
* `orderbook_builder()` - fluent API for building test `OrderBookSnapshot` objects
* `BinanceEvents` - generates synthetic Binance websocket events

Example usage:

```python
from testkit import FakeClock, FakeNotifier, orderbook_builder

# Build test orderbook data
snapshot = (
    orderbook_builder()
    .with_symbol("BTCUSDT")
    .with_bids([("45000.50", "1.5"), ("45000.00", "2.3")])
    .with_asks([("45001.00", "1.8"), ("45001.50", "2.1")])
    .build()
)

# Use fake clock for deterministic timing
clock = FakeClock(datetime(2025, 1, 1, 12, 0, 0))
clock.advance(seconds=30)

# Use fake notifier to inspect sent notifications
notifier = FakeNotifier()
await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert!")
assert notifier.was_notified("BTCUSDT")
```

---

## Tools, Commands & Plugins

If Claude Code plugins are installed in this repo, prefer:

* commands that run tests for a single package
* narrow, incremental edits
* no destructive operations unless explicitly requested and clearly local

---

## Environment Variables

Required:

* `TELEGRAM_BOT_TOKEN`            # Telegram bot token
* `TELEGRAM_CHAT_ID`              # destination chat/channel id
* `SYMBOLS`                        # comma-separated symbols (e.g. "BTCUSDT,DOTUSDT,SOLUSDT")
* `IMBALANCE_THRESHOLD`            # float X (e.g. "0.35")

Recommended:

* `TOP_N_LEVELS`                   # default 10
* `ALERT_COOLDOWN_SECONDS`         # per-symbol cooldown to avoid spam
* `BINANCE_WS_URL`                 # optional override (default: official Binance WS)
* `LOG_LEVEL`                      # INFO/DEBUG/WARN/ERROR
* `HEALTH_PORT`                    # if exposing /health

Example `.env`:

```bash
TELEGRAM_BOT_TOKEN=123:abc...
TELEGRAM_CHAT_ID=-1001234567890
SYMBOLS=BTCUSDT,DOTUSDT,SOLUSDT
IMBALANCE_THRESHOLD=0.35
TOP_N_LEVELS=10
ALERT_COOLDOWN_SECONDS=30
LOG_LEVEL=INFO
HEALTH_PORT=8080
```

---

## Common Tasks

### Add / Remove Symbols

* Update `SYMBOLS` (or config file if used).
* Ensure the connector subscribes to the correct streams and resync logic works per symbol.

### Change Alert Threshold X

* Update `IMBALANCE_THRESHOLD`.
* Add/update tests for threshold boundary conditions.

### Add Another Notification Channel

* Implement `Notifier` protocol in a new package (e.g. `notifier-slack`).
* Keep message formatting inside the notifier package.

### Add Another Exchange

* Create a new connector package (e.g. `connector-kraken`).
* Keep the normalized snapshot contract identical so the app wiring does not change.

---

## Final Notes

* Prefer small, incremental changes over large refactors.
* Keep tests passing; do not ignore failures.
* In production-like settings, be conservative with reconnect loops, backoff, and alert spam prevention.

If in doubt, propose a plan before touching code.
