FROM python:3.11-slim

WORKDIR /app

# Copy all packages
COPY packages/ packages/
COPY apps/orderbook_watcher/ apps/orderbook_watcher/

# Install dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir \
        -e packages/config \
        -e packages/domain_orderbook \
        -e packages/domain_imbalance \
        -e packages/signal_engine \
        -e packages/connector_binance \
        -e packages/notifier_telegram \
        -e packages/observability \
        -e packages/testkit \
        -e apps/orderbook_watcher

# Run the service
ENTRYPOINT ["python", "-m", "orderbook_watcher"]
