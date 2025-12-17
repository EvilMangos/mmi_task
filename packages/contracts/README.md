# contracts

Shared protocols and interfaces for the crypto orderbook alerts monorepo.

## Purpose

This package defines abstract interfaces used across the monorepo to enable loose coupling between packages. It contains
**only protocols (interfaces)** - no concrete implementations.

## Installation

```bash
pip install -e "packages/contracts[dev]"
```

## Exports

### Clock

Time abstraction protocol for dependency injection:

```python
from contracts import Clock


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current datetime."""
        ...
```

### Notifier

Notification channel protocol with structured alert payloads:

```python
from contracts import Notifier, AlertPayload


class AlertPayload(Protocol):
    symbol: str  # Trading pair (e.g., "BTCUSDT")
    ratio: float  # Imbalance ratio [-1.0, 1.0]
    bid_volume: float  # Total bid volume
    ask_volume: float  # Total ask volume
    timestamp: float  # Unix timestamp
    threshold: float  # Threshold that was exceeded


class Notifier(Protocol):
    async def send_alert(self, alert: AlertPayload) -> None:
        """Send an imbalance alert."""
        ...
```

### Exceptions

```python
from contracts import NotifierError, TransientNotifierError, PermanentNotifierError

# TransientNotifierError - retryable (network timeouts, rate limiting)
# PermanentNotifierError - non-retryable (invalid credentials, 4xx HTTP)
```

## Design Rules

- **No implementations** - only `Protocol` definitions
- **No external dependencies** - this package has zero runtime dependencies
- **Single source of truth** - all shared interfaces live here

## Testing

```bash
cd packages/contracts && pytest
```
