"""Parser for Binance WebSocket depth messages."""

import time
from decimal import Decimal, InvalidOperation
from typing import Any

from domain_orderbook import OrderBookLevel, OrderBookSnapshot

from connector_binance.exceptions import ParseError


def _parse_decimal_value(
    value: str,
    field_name: str,
    side: str,
) -> Decimal:
    """Parse and validate a decimal value from a string.

    Args:
        value: The string value to parse.
        field_name: Name of the field (e.g., 'price', 'qty') for error messages.
        side: Either 'bids' or 'asks' (for error messages).

    Returns:
        The parsed Decimal value.

    Raises:
        ParseError: If the value is empty, non-numeric, or negative.
    """
    if value == "":
        raise ParseError(f"Invalid {field_name} value in {side}: empty string")

    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ParseError(f"Invalid {field_name} value in {side}: '{value}' is not numeric")

    if result < 0:
        raise ParseError(f"Invalid {field_name} value in {side}: negative {field_name} not allowed")

    return result


def _extract_symbol_from_stream(stream_name: str) -> str:
    """Extract and normalize symbol from stream name.

    Args:
        stream_name: Stream name like 'btcusdt@depth10' or 'btcusdt@depth5@100ms'.

    Returns:
        Uppercase symbol like 'BTCUSDT'.
    """
    # Stream format: symbol@depth10 or symbol@depth5@100ms
    # Extract everything before the first '@'
    symbol_part = stream_name.split("@")[0]
    return symbol_part.upper()


def _parse_level(
    level: Any,
    side: str,
) -> OrderBookLevel:
    """Parse a single price level from Binance format.

    Args:
        level: A [price, qty] pair from Binance.
        side: Either 'bids' or 'asks' (for error messages).

    Returns:
        An OrderBookLevel instance.

    Raises:
        ParseError: If the level format is invalid or values are not valid.
    """
    if not isinstance(level, (list, tuple)) or len(level) < 2:
        raise ParseError(f"Invalid level format in {side}: expected [price, qty]")

    price_str, qty_str = level[0], level[1]

    price = _parse_decimal_value(price_str, "price", side)
    qty = _parse_decimal_value(qty_str, "qty", side)

    return OrderBookLevel(price=price, qty=qty)


def _parse_levels(
    levels: Any,
    side: str,
) -> tuple[OrderBookLevel, ...]:
    """Parse a list of price levels from Binance format.

    Args:
        levels: List of [price, qty] pairs from Binance.
        side: Either 'bids' or 'asks' (for error messages).

    Returns:
        Tuple of OrderBookLevel instances.

    Raises:
        ParseError: If any level format is invalid.
    """
    if not isinstance(levels, list):
        raise ParseError(f"Invalid {side} format: expected list")

    return tuple(_parse_level(level, side) for level in levels)


def parse_depth_message(
    message: dict[str, Any],
    symbol: str | None = None,
    timestamp: float | None = None,
) -> OrderBookSnapshot:
    """Parse a Binance depth message into an OrderBookSnapshot.

    Handles both single-stream format (direct bids/asks) and combined stream
    format (with stream and data wrapper).

    Args:
        message: The parsed JSON message from Binance WebSocket.
        symbol: Optional symbol override. If not provided, extracted from
            stream name (combined format) or required in single-stream format.
        timestamp: Optional timestamp. If not provided, current time is used.

    Returns:
        An OrderBookSnapshot instance.

    Raises:
        ParseError: If the message structure is invalid or cannot be parsed.
    """
    if not message:
        raise ParseError("Empty message")

    # Determine if this is a combined stream format or single stream
    if "stream" in message:
        # Combined stream format: {"stream": "btcusdt@depth10", "data": {...}}
        if "data" not in message:
            raise ParseError("Missing 'data' key in combined stream message")

        stream_name = message["stream"]
        data = message["data"]

        # Extract symbol from stream if not provided
        if symbol is None:
            symbol = _extract_symbol_from_stream(stream_name)
    else:
        # Single stream format: direct bids/asks at top level
        data = message

        if symbol is None:
            raise ParseError("Symbol must be provided for single-stream format messages")

    # Validate required fields
    if "bids" not in data:
        raise ParseError("Missing 'bids' key in message data")
    if "asks" not in data:
        raise ParseError("Missing 'asks' key in message data")

    # Parse levels
    bids = _parse_levels(data["bids"], "bids")
    asks = _parse_levels(data["asks"], "asks")

    # Use provided timestamp or current time
    if timestamp is None:
        timestamp = time.time()

    return OrderBookSnapshot(
        bids=bids,
        asks=asks,
        timestamp=timestamp,
        symbol=symbol,
    )
