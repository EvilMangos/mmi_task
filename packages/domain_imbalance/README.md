# domain-imbalance

Pure imbalance ratio calculation functions.

## Purpose

Computes the bid/ask volume imbalance ratio. This is a **pure** package with no external dependencies, network calls, or
I/O.

## Installation

```bash
pip install -e "packages/domain_imbalance"
```

## Formula

```
Imbalance Ratio = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)
```

- Returns a value in range `[-1.0, 1.0]`
- Positive values indicate bid-heavy (buying pressure)
- Negative values indicate ask-heavy (selling pressure)
- Zero indicates balanced order book

## Exports

```python
from domain_imbalance import imbalance_ratio, imbalance_from_levels
```

### imbalance_ratio

Calculate ratio from pre-computed volumes:

```python
from domain_imbalance import imbalance_ratio

ratio = imbalance_ratio(bid_volume=150.0, ask_volume=100.0)
# Returns: 0.2 (positive = more bids)

ratio = imbalance_ratio(bid_volume=100.0, ask_volume=100.0)
# Returns: 0.0 (balanced)

ratio = imbalance_ratio(bid_volume=0.0, ask_volume=0.0)
# Returns: 0.0 (edge case: empty book)
```

### imbalance_from_levels

Calculate ratio directly from order book levels:

```python
from domain_imbalance import imbalance_from_levels
from domain_orderbook import OrderBookLevel

bids = [OrderBookLevel(price=100, quantity=10)]
asks = [OrderBookLevel(price=101, quantity=5)]

ratio = imbalance_from_levels(bids, asks)
# Returns: 0.333... (more bid volume)
```

## Design Rules

- **Pure functions only** - deterministic, no side effects
- **Edge case handling** - returns 0.0 for empty/zero volumes
- **No external dependencies** - stdlib only

## Testing

```bash
cd packages/domain_imbalance && pytest
```
