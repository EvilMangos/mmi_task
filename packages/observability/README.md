# observability

Logging, metrics, and tracing utilities.

## Purpose

Provides standardized observability primitives for the monorepo:

- Structured JSON logging
- Prometheus-compatible metrics
- Correlation ID tracking
- Exception formatting

## Installation

```bash
pip install -e "packages/observability[dev]"
```

## Exports

### Logging

```python
from observability import get_logger, JsonFormatter

logger = get_logger(__name__)
logger.info("Processing snapshot", extra={"symbol": "BTCUSDT"})
```

### Debug Mode

```python
from observability import is_debug_enabled

if is_debug_enabled():
    logger.debug("Verbose output...")
```

### Correlation IDs

Track requests across async operations:

```python
from observability import (
    correlation_context,
    get_correlation_id,
    set_correlation_id,
    reset_correlation_id,
)

# Context manager for automatic cleanup
async with correlation_context("req-123"):
    logger.info("Processing")  # Logs include correlation_id

# Manual management
set_correlation_id("req-456")
current = get_correlation_id()
reset_correlation_id()
```

### Exception Formatting

```python
from observability import format_exception

try:
    risky_operation()
except Exception as e:
    formatted = format_exception(e)
    logger.error("Operation failed", extra={"error": formatted})
```

### Timing

```python
from observability import timed


@timed
async def process_data():
    ...  # Logs execution time
```

### Metrics

Prometheus-compatible metrics:

```python
from observability import Counter, Gauge, MetricsRegistry, format_prometheus

registry = MetricsRegistry()

# Counter (monotonic)
alerts_sent = Counter("alerts_sent", "Total alerts sent", registry)
alerts_sent.inc()
alerts_sent.inc(labels={"symbol": "BTCUSDT"})

# Gauge (can go up/down)
active_connections = Gauge("active_connections", "Current connections", registry)
active_connections.set(5)
active_connections.inc()
active_connections.dec()

# Export to Prometheus format
output = format_prometheus(registry)
```

## Testing

```bash
cd packages/observability && pytest
```

## Configuration

| Variable    | Default | Description       |
|-------------|---------|-------------------|
| `LOG_LEVEL` | `INFO`  | Logging level     |
| `DEBUG`     | `false` | Enable debug mode |
