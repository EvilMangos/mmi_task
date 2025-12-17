# domain-orderbook

Pure order book types and helper functions.

## Purpose

Provides domain types for representing order book data and functions for normalizing and querying order book levels.
This is a **pure** package with no external dependencies, network calls, or I/O.

## Installation

```bash
pip install -e "packages/domain_orderbook"
```

## Exports

### Types

```python
from domain_orderbook import OrderBookLevel, OrderBookSnapshot
```

**OrderBookLevel** - A single price/quantity level:

```python
level = OrderBookLevel(price=Decimal("45000.50"), quantity=Decimal("1.5"))
```

**OrderBookSnapshot** - Point-in-time order book state:

```python
snapshot = OrderBookSnapshot(
    symbol="BTCUSDT",
    bids=[OrderBookLevel(...)],
    asks=[OrderBookLevel(...)],
    timestamp=1704067200.0,
)
```

### Helper Functions

```python
from domain_orderbook import (
    normalize_bids,  # Sort bids descending by price
    normalize_asks,  # Sort asks ascending by price
    top_n_bids,  # Get top N bid levels
    top_n_asks,  # Get top N ask levels
    sum_volume,  # Sum quantities across levels
)
```

## Usage

```python
from domain_orderbook import OrderBookSnapshot, top_n_bids, top_n_asks, sum_volume

# Extract top 10 levels
top_bids = top_n_bids(snapshot.bids, n=10)
top_asks = top_n_asks(snapshot.asks, n=10)

# Calculate total volumes
bid_volume = sum_volume(top_bids)
ask_volume = sum_volume(top_asks)
```

## Design Rules

- **Pure functions only** - no side effects, network calls, or time access
- **Decimal precision** - prices and quantities use `Decimal` for accuracy
- **No external dependencies** - stdlib only

## Testing

```bash
cd packages/domain_orderbook && pytest
```
