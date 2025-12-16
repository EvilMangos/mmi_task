"""
Tests for parse_depth_message - TDD RED stage.

These tests define the expected behavior of the message parser that converts
raw Binance WebSocket depth messages to OrderBookSnapshot instances.

Requirements covered:
    R1: Parse valid single-stream depth message
    R2: Parse combined stream format (stream + data keys)
    R3: Extract symbol from stream name (btcusdt@depth10 -> BTCUSDT)
    R4: Convert string prices to Decimal
    R5: Convert string quantities to Decimal
    R6: Create correct OrderBookLevel instances
    R7: Handle empty bids/asks arrays
    R8: Raise ParseError on malformed JSON structure
    R9: Raise ParseError on invalid price values
    R10: Raise ParseError on invalid quantity values
"""

from decimal import Decimal

import pytest
from domain_orderbook import OrderBookLevel, OrderBookSnapshot

# These imports will fail until implementation exists (RED stage)
from connector_binance.exceptions import ParseError
from connector_binance.message_parser import parse_depth_message

# =============================================================================
# Fixtures - Sample Binance Messages
# =============================================================================


@pytest.fixture
def single_stream_message() -> dict:
    """Single stream partial depth message from Binance."""
    return {
        "lastUpdateId": 160,
        "bids": [
            ["0.0024", "10"],
            ["0.0023", "20"],
        ],
        "asks": [
            ["0.0026", "100"],
            ["0.0027", "50"],
        ],
    }


@pytest.fixture
def combined_stream_message() -> dict:
    """Combined stream message with wrapper."""
    return {
        "stream": "btcusdt@depth10",
        "data": {
            "lastUpdateId": 160,
            "bids": [
                ["42000.50", "1.5"],
                ["42000.00", "2.0"],
            ],
            "asks": [
                ["42001.00", "0.5"],
                ["42001.50", "1.0"],
            ],
        },
    }


@pytest.fixture
def combined_stream_message_solusdt() -> dict:
    """Combined stream message for SOLUSDT."""
    return {
        "stream": "solusdt@depth10",
        "data": {
            "lastUpdateId": 500,
            "bids": [
                ["150.25", "100"],
            ],
            "asks": [
                ["150.30", "50"],
            ],
        },
    }


@pytest.fixture
def message_with_empty_bids() -> dict:
    """Message with empty bids array."""
    return {
        "stream": "btcusdt@depth10",
        "data": {
            "lastUpdateId": 161,
            "bids": [],
            "asks": [
                ["42001.00", "0.5"],
            ],
        },
    }


@pytest.fixture
def message_with_empty_asks() -> dict:
    """Message with empty asks array."""
    return {
        "stream": "btcusdt@depth10",
        "data": {
            "lastUpdateId": 162,
            "bids": [
                ["42000.50", "1.5"],
            ],
            "asks": [],
        },
    }


@pytest.fixture
def high_precision_message() -> dict:
    """Message with high precision decimal values."""
    return {
        "stream": "dotusdt@depth10",
        "data": {
            "lastUpdateId": 300,
            "bids": [
                ["7.12345678", "1234.56789012"],
            ],
            "asks": [
                ["7.12345679", "9876.54321098"],
            ],
        },
    }


# =============================================================================
# Category 1: Valid Message Parsing (R1, R2)
# =============================================================================


class TestValidMessageParsing:
    """Tests for parsing valid Binance messages."""

    def test_parse_valid_depth_message(self, single_stream_message: dict) -> None:
        """R1: Parse standard Binance depth message with explicit symbol."""
        snapshot = parse_depth_message(
            message=single_stream_message,
            symbol="BTCUSDT",
        )

        assert isinstance(snapshot, OrderBookSnapshot)
        assert snapshot.symbol == "BTCUSDT"
        assert len(snapshot.bids) == 2
        assert len(snapshot.asks) == 2

    def test_parse_combined_stream_message(self, combined_stream_message: dict) -> None:
        """R2: Parse wrapped combined stream format with stream and data keys."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert isinstance(snapshot, OrderBookSnapshot)
        assert snapshot.symbol == "BTCUSDT"
        assert len(snapshot.bids) == 2
        assert len(snapshot.asks) == 2

    def test_parses_all_bid_levels(self, combined_stream_message: dict) -> None:
        """R1: All bid levels are parsed correctly."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert len(snapshot.bids) == 2
        assert snapshot.bids[0].price == Decimal("42000.50")
        assert snapshot.bids[0].qty == Decimal("1.5")
        assert snapshot.bids[1].price == Decimal("42000.00")
        assert snapshot.bids[1].qty == Decimal("2.0")

    def test_parses_all_ask_levels(self, combined_stream_message: dict) -> None:
        """R1: All ask levels are parsed correctly."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert len(snapshot.asks) == 2
        assert snapshot.asks[0].price == Decimal("42001.00")
        assert snapshot.asks[0].qty == Decimal("0.5")
        assert snapshot.asks[1].price == Decimal("42001.50")
        assert snapshot.asks[1].qty == Decimal("1.0")


# =============================================================================
# Category 2: Symbol Extraction (R3)
# =============================================================================


class TestSymbolExtraction:
    """Tests for symbol extraction from stream names."""

    def test_extracts_symbol_from_stream_name(
        self, combined_stream_message: dict
    ) -> None:
        """R3: Symbol extracted from btcusdt@depth10 -> BTCUSDT."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert snapshot.symbol == "BTCUSDT"

    def test_extracts_symbol_from_solusdt_stream(
        self, combined_stream_message_solusdt: dict
    ) -> None:
        """R3: Symbol extracted from solusdt@depth10 -> SOLUSDT."""
        snapshot = parse_depth_message(message=combined_stream_message_solusdt)

        assert snapshot.symbol == "SOLUSDT"

    def test_explicit_symbol_overrides_stream_name(
        self, combined_stream_message: dict
    ) -> None:
        """R3: Explicit symbol parameter takes precedence over stream name."""
        snapshot = parse_depth_message(
            message=combined_stream_message,
            symbol="ETHUSDT",  # Override
        )

        assert snapshot.symbol == "ETHUSDT"

    @pytest.mark.parametrize(
        "stream_name,expected_symbol",
        [
            ("btcusdt@depth5", "BTCUSDT"),
            ("ethusdt@depth10", "ETHUSDT"),
            ("dotusdt@depth20", "DOTUSDT"),
            ("bnbusdt@depth5@100ms", "BNBUSDT"),
        ],
    )
    def test_various_stream_name_formats(
        self, stream_name: str, expected_symbol: str
    ) -> None:
        """R3: Various stream name formats extract symbol correctly."""
        message = {
            "stream": stream_name,
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0", "1.0"]],
                "asks": [["1.1", "1.0"]],
            },
        }

        snapshot = parse_depth_message(message=message)

        assert snapshot.symbol == expected_symbol


# =============================================================================
# Category 3: Decimal Conversion (R4, R5)
# =============================================================================


class TestDecimalConversion:
    """Tests for string to Decimal conversion."""

    def test_converts_price_to_decimal(self, combined_stream_message: dict) -> None:
        """R4: String prices converted to Decimal accurately."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert snapshot.bids[0].price == Decimal("42000.50")
        assert isinstance(snapshot.bids[0].price, Decimal)

    def test_converts_qty_to_decimal(self, combined_stream_message: dict) -> None:
        """R5: String quantities converted to Decimal accurately."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert snapshot.bids[0].qty == Decimal("1.5")
        assert isinstance(snapshot.bids[0].qty, Decimal)

    def test_high_precision_decimals_preserved(
        self, high_precision_message: dict
    ) -> None:
        """R4/R5: High precision decimal values are preserved exactly."""
        snapshot = parse_depth_message(message=high_precision_message)

        assert snapshot.bids[0].price == Decimal("7.12345678")
        assert snapshot.bids[0].qty == Decimal("1234.56789012")
        assert snapshot.asks[0].price == Decimal("7.12345679")
        assert snapshot.asks[0].qty == Decimal("9876.54321098")

    def test_integer_strings_converted_correctly(self) -> None:
        """R4/R5: Integer string values convert to Decimal correctly."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["42000", "10"]],
                "asks": [["42001", "5"]],
            },
        }

        snapshot = parse_depth_message(message=message)

        assert snapshot.bids[0].price == Decimal("42000")
        assert snapshot.bids[0].qty == Decimal("10")

    def test_zero_values_converted_correctly(self) -> None:
        """R4/R5: Zero values convert correctly."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["0.0", "0"]],
                "asks": [["0", "0.0"]],
            },
        }

        snapshot = parse_depth_message(message=message)

        assert snapshot.bids[0].price == Decimal("0")
        assert snapshot.bids[0].qty == Decimal("0")


# =============================================================================
# Category 4: OrderBookLevel Creation (R6)
# =============================================================================


class TestOrderBookLevelCreation:
    """Tests for proper OrderBookLevel instance creation."""

    def test_creates_correct_orderbooklevels(
        self, combined_stream_message: dict
    ) -> None:
        """R6: Proper OrderBookLevel instances are created."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert all(isinstance(level, OrderBookLevel) for level in snapshot.bids)
        assert all(isinstance(level, OrderBookLevel) for level in snapshot.asks)

    def test_level_count_matches_input(self) -> None:
        """R6: Number of levels matches input."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0", "1"], ["2.0", "2"], ["3.0", "3"]],
                "asks": [["4.0", "4"], ["5.0", "5"]],
            },
        }

        snapshot = parse_depth_message(message=message)

        assert len(snapshot.bids) == 3
        assert len(snapshot.asks) == 2

    def test_levels_are_tuples_not_lists(self, combined_stream_message: dict) -> None:
        """R6: Bids and asks are tuples (immutable)."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert isinstance(snapshot.bids, tuple)
        assert isinstance(snapshot.asks, tuple)


# =============================================================================
# Category 5: Empty Arrays (R7)
# =============================================================================


class TestEmptyArrays:
    """Tests for empty bids/asks handling."""

    def test_handles_empty_bids(self, message_with_empty_bids: dict) -> None:
        """R7: Empty bids array produces empty tuple."""
        snapshot = parse_depth_message(message=message_with_empty_bids)

        assert snapshot.bids == ()
        assert len(snapshot.asks) == 1

    def test_handles_empty_asks(self, message_with_empty_asks: dict) -> None:
        """R7: Empty asks array produces empty tuple."""
        snapshot = parse_depth_message(message=message_with_empty_asks)

        assert snapshot.asks == ()
        assert len(snapshot.bids) == 1

    def test_handles_both_empty(self) -> None:
        """R7: Both empty bids and asks handled."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [],
                "asks": [],
            },
        }

        snapshot = parse_depth_message(message=message)

        assert snapshot.bids == ()
        assert snapshot.asks == ()


# =============================================================================
# Category 6: Malformed JSON Structure (R8)
# =============================================================================


class TestMalformedJsonStructure:
    """Tests for error handling on malformed JSON."""

    def test_raises_on_malformed_json_structure_missing_bids(self) -> None:
        """R8: Missing bids key raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "asks": [["1.0", "1"]],
                # missing "bids"
            },
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert "bids" in str(exc_info.value).lower()

    def test_raises_on_malformed_json_structure_missing_asks(self) -> None:
        """R8: Missing asks key raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0", "1"]],
                # missing "asks"
            },
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert "asks" in str(exc_info.value).lower()

    def test_raises_on_missing_data_in_combined_stream(self) -> None:
        """R8: Missing data key in combined stream raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            # missing "data"
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "data" in str(exc_info.value).lower()
            or "structure" in str(exc_info.value).lower()
        )

    def test_raises_on_empty_message(self) -> None:
        """R8: Empty message raises ParseError."""
        with pytest.raises(ParseError):
            parse_depth_message(message={})

    def test_raises_on_invalid_level_format(self) -> None:
        """R8: Level with wrong number of elements raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0"]],  # Missing quantity
                "asks": [["1.0", "1"]],
            },
        }

        with pytest.raises(ParseError):
            parse_depth_message(message=message)


# =============================================================================
# Category 7: Invalid Price Values (R9)
# =============================================================================


class TestInvalidPriceValues:
    """Tests for error handling on invalid price values."""

    def test_raises_on_invalid_price_value_non_numeric(self) -> None:
        """R9: Non-numeric price raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["not_a_number", "1.0"]],
                "asks": [["1.0", "1.0"]],
            },
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert "price" in str(exc_info.value).lower()

    def test_raises_on_negative_price(self) -> None:
        """R9: Negative price raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["-1.0", "1.0"]],
                "asks": [["1.0", "1.0"]],
            },
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "price" in str(exc_info.value).lower()
            or "negative" in str(exc_info.value).lower()
        )

    def test_raises_on_empty_price_string(self) -> None:
        """R9: Empty price string raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["", "1.0"]],
                "asks": [["1.0", "1.0"]],
            },
        }

        with pytest.raises(ParseError):
            parse_depth_message(message=message)


# =============================================================================
# Category 8: Invalid Quantity Values (R10)
# =============================================================================


class TestInvalidQuantityValues:
    """Tests for error handling on invalid quantity values."""

    def test_raises_on_invalid_qty_value_non_numeric(self) -> None:
        """R10: Non-numeric qty raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0", "invalid"]],
                "asks": [["1.0", "1.0"]],
            },
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "qty" in str(exc_info.value).lower()
            or "quantity" in str(exc_info.value).lower()
        )

    def test_raises_on_negative_qty(self) -> None:
        """R10: Negative qty raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0", "-5.0"]],
                "asks": [["1.0", "1.0"]],
            },
        }

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "qty" in str(exc_info.value).lower()
            or "negative" in str(exc_info.value).lower()
        )

    def test_raises_on_empty_qty_string(self) -> None:
        """R10: Empty qty string raises ParseError."""
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0", ""]],
                "asks": [["1.0", "1.0"]],
            },
        }

        with pytest.raises(ParseError):
            parse_depth_message(message=message)


# =============================================================================
# Timestamp Handling
# =============================================================================


class TestTimestampHandling:
    """Tests for timestamp assignment in snapshots."""

    def test_snapshot_has_valid_timestamp(self, combined_stream_message: dict) -> None:
        """Snapshot includes a valid timestamp."""
        snapshot = parse_depth_message(message=combined_stream_message)

        assert isinstance(snapshot.timestamp, float)
        assert snapshot.timestamp >= 0

    def test_explicit_timestamp_used_when_provided(
        self, combined_stream_message: dict
    ) -> None:
        """Explicit timestamp parameter is used."""
        snapshot = parse_depth_message(
            message=combined_stream_message,
            timestamp=1234567890.123,
        )

        assert snapshot.timestamp == 1234567890.123
