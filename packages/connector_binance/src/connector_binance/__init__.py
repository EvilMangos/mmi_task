"""Binance WS/REST client, emits normalized order book events."""

from connector_binance.backoff import ExponentialBackoff
from connector_binance.binance_feed import BinanceFeed
from connector_binance.exceptions import ParseError
from connector_binance.message_parser import parse_depth_message

__all__ = [
    "BinanceFeed",
    "ExponentialBackoff",
    "ParseError",
    "parse_depth_message",
]
