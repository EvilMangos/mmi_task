# testkit

Shared test fixtures, fakes, and builders for the monorepo.

## Purpose

Provides reusable testing utilities including:

- Fake implementations of protocols
- Test data builders with fluent APIs
- Synthetic event generators
- Shared pytest fixtures

## Installation

```bash
pip install -e "packages/testkit[dev]"
```

## Dependencies

- `contracts` - Clock protocol
- `domain-orderbook` - Snapshot types

## Exports

```python
from testkit import (
    FakeClock,
    FakeNotifier,
    BinanceEvents,
    OrderBookBuilder,
    orderbook_builder,
)
```

### FakeClock

Injectable time source for deterministic tests:

```python
from testkit import FakeClock
from datetime import datetime, timedelta

clock = FakeClock(datetime(2025, 1, 1, 12, 0, 0))

assert clock.now() == datetime(2025, 1, 1, 12, 0, 0)

clock.advance(seconds=30)
assert clock.now() == datetime(2025, 1, 1, 12, 0, 30)

clock.advance(timedelta(minutes=5))
assert clock.now() == datetime(2025, 1, 1, 12, 5, 30)
```

### FakeNotifier

Records notification calls for inspection:

```python
from testkit import FakeNotifier

notifier = FakeNotifier()

# Send alerts
await notifier.notify(symbol="BTCUSDT", ratio=0.5, message="Alert!")

# Inspect calls
assert notifier.was_notified("BTCUSDT")
assert notifier.call_count == 1
assert notifier.last_call == ("BTCUSDT", 0.5, "Alert!")
assert notifier.messages == ["Alert!"]

# Filter by symbol
btc_calls = notifier.get_calls_for_symbol("BTCUSDT")

# Simulate errors
notifier.set_error(ConnectionError("Network failure"))
with pytest.raises(ConnectionError):
    await notifier.notify(...)
notifier.clear_error()

# Reset state
notifier.reset()
```

### OrderBookBuilder

Fluent API for building test snapshots:

```python
from testkit import orderbook_builder

# Explicit levels
snapshot = (
    orderbook_builder()
    .with_symbol("BTCUSDT")
    .with_bids([("45000.50", "1.5"), ("45000.00", "2.3")])
    .with_asks([("45001.00", "1.8"), ("45001.50", "2.1")])
    .build()
)

# Set both sides at once
snapshot = orderbook_builder().with_levels(
    bids=[("100.00", "5.0")],
    asks=[("100.01", "5.0")],
).build()

# Single-level shortcuts
snapshot = (
    orderbook_builder()
    .with_single_bid("100.00", "10.0")
    .with_single_ask("100.01", "5.0")
    .build()
)

# Target a specific imbalance ratio
snapshot = orderbook_builder().with_imbalance_ratio(0.5).build()

# Convenience presets
snapshot = orderbook_builder().with_balanced_book().build()  # ratio = 0.0
snapshot = orderbook_builder().with_high_bid_imbalance().build()  # ratio = 0.6
snapshot = orderbook_builder().with_high_ask_imbalance().build()  # ratio = -0.6
```

### BinanceEvents

Generate synthetic Binance protocol events:

```python
from testkit import BinanceEvents

# Default: timestamps start at 2024-01-01 00:00:00 UTC
events = BinanceEvents()

# Depth update event
update = events.depth_update(
    symbol="BTCUSDT",
    bids=[("45000.00", "1.5")],
    asks=[("45001.00", "1.2")],
)

# Snapshot response
snapshot = events.snapshot(
    symbol="BTCUSDT",
    bids=[("45000.00", "1.5")],
    asks=[("45001.00", "1.2")],
)

# Sequence of events
sequence = events.sequence(
    symbol="BTCUSDT",
    updates=[
        {"bids": [("45000.00", "1.5")], "asks": [("45001.00", "1.2")]},
        {"bids": [("45000.00", "2.0")], "asks": [("45001.00", "1.0")]},
    ],
)
```

## Pytest Fixtures

The package provides ready-to-use fixtures in `conftest.py`:

```python
from testkit.conftest import DEFAULT_TEST_DATETIME, DEFAULT_SYMBOL


def test_with_fake_clock(fake_clock):
    assert fake_clock.now() == DEFAULT_TEST_DATETIME
    fake_clock.advance(seconds=30)


async def test_with_fake_notifier(fake_notifier):
    await fake_notifier.notify(symbol=DEFAULT_SYMBOL, ratio=0.5, message="Test")
    assert fake_notifier.was_notified(DEFAULT_SYMBOL)


def test_with_binance_events(binance_events):
    event = binance_events.depth_update(symbol="BTCUSDT", bids=[], asks=[])
```

### Shared Constants

- `DEFAULT_TEST_DATETIME` = `datetime(2025, 1, 1, 12, 0, 0)`
- `DEFAULT_SYMBOL` = `"BTCUSDT"`

## Testing

```bash
cd packages/testkit && pytest
```
