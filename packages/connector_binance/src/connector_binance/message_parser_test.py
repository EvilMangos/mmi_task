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
# Fixtures - Sample Binance Messages (using BinanceMessageBuilder)
# =============================================================================


@pytest.fixture
def single_stream_message(binance_message_builder) -> dict:
    """Single stream partial depth message from Binance."""
    return (
        binance_message_builder()
        .with_last_update_id(160)
        .with_bids([("0.0024", "10"), ("0.0023", "20")])
        .with_asks([("0.0026", "100"), ("0.0027", "50")])
        .build_single_stream()
    )


@pytest.fixture
def combined_stream_message(binance_message_builder) -> dict:
    """Combined stream message with wrapper."""
    return (
        binance_message_builder()
        .with_symbol("BTCUSDT")
        .with_last_update_id(160)
        .with_bids([("42000.50", "1.5"), ("42000.00", "2.0")])
        .with_asks([("42001.00", "0.5"), ("42001.50", "1.0")])
        .build()
    )


@pytest.fixture
def combined_stream_message_solusdt(binance_message_builder) -> dict:
    """Combined stream message for SOLUSDT."""
    return (
        binance_message_builder()
        .with_symbol("SOLUSDT")
        .with_last_update_id(500)
        .with_bids([("150.25", "100")])
        .with_asks([("150.30", "50")])
        .build()
    )


@pytest.fixture
def message_with_empty_bids(binance_message_builder) -> dict:
    """Message with empty bids array."""
    return (
        binance_message_builder()
        .with_symbol("BTCUSDT")
        .with_last_update_id(161)
        .with_bids([])
        .with_asks([("42001.00", "0.5")])
        .build()
    )


@pytest.fixture
def message_with_empty_asks(binance_message_builder) -> dict:
    """Message with empty asks array."""
    return (
        binance_message_builder()
        .with_symbol("BTCUSDT")
        .with_last_update_id(162)
        .with_bids([("42000.50", "1.5")])
        .with_asks([])
        .build()
    )


@pytest.fixture
def high_precision_message(binance_message_builder) -> dict:
    """Message with high precision decimal values."""
    return (
        binance_message_builder()
        .with_symbol("DOTUSDT")
        .with_last_update_id(300)
        .with_bids([("7.12345678", "1234.56789012")])
        .with_asks([("7.12345679", "9876.54321098")])
        .build()
    )


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
        self, binance_message_builder, stream_name: str, expected_symbol: str
    ) -> None:
        """R3: Various stream name formats extract symbol correctly."""
        message = (
            binance_message_builder()
            .with_stream(stream_name)
            .with_bids([("1.0", "1.0")])
            .with_asks([("1.1", "1.0")])
            .build()
        )

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

    def test_integer_strings_converted_correctly(self, binance_message_builder) -> None:
        """R4/R5: Integer string values convert to Decimal correctly."""
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("42000", "10")])
            .with_asks([("42001", "5")])
            .build()
        )

        snapshot = parse_depth_message(message=message)

        assert snapshot.bids[0].price == Decimal("42000")
        assert snapshot.bids[0].qty == Decimal("10")

    def test_zero_values_converted_correctly(self, binance_message_builder) -> None:
        """R4/R5: Zero values convert correctly."""
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("0.0", "0")])
            .with_asks([("0", "0.0")])
            .build()
        )

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

    def test_level_count_matches_input(self, binance_message_builder) -> None:
        """R6: Number of levels matches input."""
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("1.0", "1"), ("2.0", "2"), ("3.0", "3")])
            .with_asks([("4.0", "4"), ("5.0", "5")])
            .build()
        )

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

    def test_handles_both_empty(self, binance_message_builder) -> None:
        """R7: Both empty bids and asks handled."""
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([])
            .with_asks([])
            .build()
        )

        snapshot = parse_depth_message(message=message)

        assert snapshot.bids == ()
        assert snapshot.asks == ()


# =============================================================================
# Category 6: Malformed JSON Structure (R8)
# =============================================================================


class TestMalformedJsonStructure:
    """Tests for error handling on malformed JSON."""

    def test_raises_on_malformed_json_structure_missing_bids(
        self, binance_message_builder
    ) -> None:
        """R8: Missing bids key raises ParseError."""
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_asks([("1.0", "1")])
            .build_without_bids()
        )

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert "bids" in str(exc_info.value).lower()

    def test_raises_on_malformed_json_structure_missing_asks(
        self, binance_message_builder
    ) -> None:
        """R8: Missing asks key raises ParseError."""
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("1.0", "1")])
            .build_without_asks()
        )

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert "asks" in str(exc_info.value).lower()

    def test_raises_on_missing_data_in_combined_stream(
        self, binance_message_builder
    ) -> None:
        """R8: Missing data key in combined stream raises ParseError."""
        message = binance_message_builder().with_symbol("BTCUSDT").build_without_data()

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

    def test_raises_on_invalid_level_format(self, binance_message_builder) -> None:
        """R8: Level with wrong number of elements raises ParseError."""
        # Build a valid message first, then manually modify bids to have invalid format
        # The builder doesn't support invalid formats by design, so we construct manually
        message = {
            "stream": "btcusdt@depth10",
            "data": {
                "lastUpdateId": 100,
                "bids": [["1.0"]],  # Missing quantity - intentionally invalid
                "asks": [["1.0", "1"]],
            },
        }

        with pytest.raises(ParseError):
            parse_depth_message(message=message)


# =============================================================================
# Category 7: Invalid Price Values (R9)
# =============================================================================


class TestInvalidPriceValues:
    """Tests for error handling on invalid price values.

    Note: These tests intentionally construct invalid messages manually rather than
    using BinanceMessageBuilder, since the builder is designed to produce valid data.
    """

    def test_raises_on_invalid_price_value_non_numeric(
        self, binance_message_builder
    ) -> None:
        """R9: Non-numeric price raises ParseError."""
        # Intentionally invalid - builder cannot produce this
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("not_a_number", "1.0")])
            .with_asks([("1.0", "1.0")])
            .build()
        )

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert "price" in str(exc_info.value).lower()

    def test_raises_on_negative_price(self, binance_message_builder) -> None:
        """R9: Negative price raises ParseError."""
        # Intentionally invalid - negative price
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("-1.0", "1.0")])
            .with_asks([("1.0", "1.0")])
            .build()
        )

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "price" in str(exc_info.value).lower()
            or "negative" in str(exc_info.value).lower()
        )

    def test_raises_on_empty_price_string(self, binance_message_builder) -> None:
        """R9: Empty price string raises ParseError."""
        # Intentionally invalid - empty price string
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("", "1.0")])
            .with_asks([("1.0", "1.0")])
            .build()
        )

        with pytest.raises(ParseError):
            parse_depth_message(message=message)


# =============================================================================
# Category 8: Invalid Quantity Values (R10)
# =============================================================================


class TestInvalidQuantityValues:
    """Tests for error handling on invalid quantity values.

    Note: These tests intentionally construct invalid messages using the builder
    with invalid data to test error handling.
    """

    def test_raises_on_invalid_qty_value_non_numeric(
        self, binance_message_builder
    ) -> None:
        """R10: Non-numeric qty raises ParseError."""
        # Intentionally invalid - non-numeric quantity
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("1.0", "invalid")])
            .with_asks([("1.0", "1.0")])
            .build()
        )

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "qty" in str(exc_info.value).lower()
            or "quantity" in str(exc_info.value).lower()
        )

    def test_raises_on_negative_qty(self, binance_message_builder) -> None:
        """R10: Negative qty raises ParseError."""
        # Intentionally invalid - negative quantity
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("1.0", "-5.0")])
            .with_asks([("1.0", "1.0")])
            .build()
        )

        with pytest.raises(ParseError) as exc_info:
            parse_depth_message(message=message)

        assert (
            "qty" in str(exc_info.value).lower()
            or "negative" in str(exc_info.value).lower()
        )

    def test_raises_on_empty_qty_string(self, binance_message_builder) -> None:
        """R10: Empty qty string raises ParseError."""
        # Intentionally invalid - empty quantity string
        message = (
            binance_message_builder()
            .with_symbol("BTCUSDT")
            .with_bids([("1.0", "")])
            .with_asks([("1.0", "1.0")])
            .build()
        )

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
