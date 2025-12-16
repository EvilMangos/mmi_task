"""Custom exceptions for the Binance connector."""


class ParseError(Exception):
    """Raised when parsing a Binance message fails.

    This exception indicates that a message received from Binance WebSocket
    could not be parsed into the expected format.
    """

    pass
