# signal-engine

Threshold evaluation, cooldown, and alert decision logic.

## Purpose

Determines whether an imbalance ratio should trigger an alert, considering:

- Threshold comparison
- Per-symbol cooldown to prevent alert spam
- Optional hysteresis to avoid flapping

## Installation

```bash
pip install -e "packages/signal_engine"
```

## Dependencies

- `contracts` - Clock protocol
- `domain-imbalance` - Imbalance calculations

## Exports

```python
from signal_engine import SignalEvaluator, EngineConfig, AlertDecision, Clock
```

### EngineConfig

Configuration for the signal evaluator:

```python
from signal_engine import EngineConfig

config = EngineConfig(
    threshold=0.35,  # Alert when |ratio| > threshold
    cooldown_seconds=30.0,  # Per-symbol cooldown
    hysteresis_enabled=False,  # Optional flapping prevention
)
```

### SignalEvaluator

Stateful evaluator with per-symbol cooldown tracking:

```python
from signal_engine import SignalEvaluator, EngineConfig

config = EngineConfig(threshold=0.35, cooldown_seconds=30.0)
evaluator = SignalEvaluator(config, clock)

# Evaluate a ratio for a symbol
decision = evaluator.evaluate(symbol="BTCUSDT", ratio=0.42)

if decision.should_alert:
    print(f"Alert! Reason: {decision.reason}")
else:
    print(f"No alert: {decision.reason}")
```

### AlertDecision

Result of evaluation:

```python
from signal_engine import AlertDecision

decision = AlertDecision(
    should_alert=True,
    reason="threshold_exceeded",
)
```

## Behavior

1. **Threshold Check**: Alerts only when `|ratio| > threshold`
2. **Cooldown**: After alerting, the same symbol won't trigger again until cooldown expires
3. **Hysteresis** (optional): Prevents rapid on/off flapping near threshold

## Design Rules

- Uses injected `Clock` for deterministic testing
- Maintains per-symbol state internally
- No I/O or external calls

## Testing

```bash
cd packages/signal_engine && pytest
```

Use `FakeClock` from `testkit` for deterministic time control in tests.
