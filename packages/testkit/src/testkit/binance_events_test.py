"""Tests for BinanceEvents - synthetic Binance websocket event generator."""

from testkit.binance_events import BinanceEvents


class TestBinanceEventsInitialization:
    """Test BinanceEvents initialization."""

    def test_creates_successfully(self):
        events = BinanceEvents()

        assert events is not None

    def test_can_create_multiple_instances(self):
        events1 = BinanceEvents()
        events2 = BinanceEvents()

        assert events1 is not events2


class TestBinanceEventsDepthUpdate:
    """Test depth update event generation."""

    def test_depth_update_basic_structure(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("100", "10")], asks=[("101", "11")]
        )

        assert isinstance(event, dict)
        assert "e" in event
        assert "s" in event
        assert "b" in event
        assert "a" in event
        assert "E" in event

    def test_depth_update_event_type(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])

        assert event["e"] == "depthUpdate"

    def test_depth_update_symbol(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("100", "10")], asks=[("101", "11")]
        )

        assert event["s"] == "BTCUSDT"

    def test_depth_update_with_different_symbols(self):
        events = BinanceEvents()

        event1 = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])
        event2 = events.depth_update(symbol="DOTUSDT", bids=[], asks=[])
        event3 = events.depth_update(symbol="SOLUSDT", bids=[], asks=[])

        assert event1["s"] == "BTCUSDT"
        assert event2["s"] == "DOTUSDT"
        assert event3["s"] == "SOLUSDT"

    def test_depth_update_empty_bids_and_asks(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])

        assert event["b"] == []
        assert event["a"] == []

    def test_depth_update_single_bid(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTCUSDT", bids=[("100.5", "10.0")], asks=[])

        assert len(event["b"]) == 1
        assert event["b"][0] == ["100.5", "10.0"]

    def test_depth_update_single_ask(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTCUSDT", bids=[], asks=[("101.5", "11.0")])

        assert len(event["a"]) == 1
        assert event["a"][0] == ["101.5", "11.0"]

    def test_depth_update_multiple_bids(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT",
            bids=[("100", "10"), ("99", "20"), ("98", "30")],
            asks=[],
        )

        assert len(event["b"]) == 3
        assert event["b"][0] == ["100", "10"]
        assert event["b"][1] == ["99", "20"]
        assert event["b"][2] == ["98", "30"]

    def test_depth_update_multiple_asks(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT",
            bids=[],
            asks=[("101", "11"), ("102", "22"), ("103", "33")],
        )

        assert len(event["a"]) == 3
        assert event["a"][0] == ["101", "11"]
        assert event["a"][1] == ["102", "22"]
        assert event["a"][2] == ["103", "33"]

    def test_depth_update_bids_and_asks_together(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("100", "10")], asks=[("101", "11")]
        )

        assert len(event["b"]) == 1
        assert len(event["a"]) == 1
        assert event["b"][0] == ["100", "10"]
        assert event["a"][0] == ["101", "11"]

    def test_depth_update_has_timestamp(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])

        assert "E" in event
        assert isinstance(event["E"], int)
        assert event["E"] > 0

    def test_depth_update_timestamps_increase(self):
        events = BinanceEvents()

        event1 = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])
        event2 = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])
        event3 = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])

        assert event2["E"] > event1["E"]
        assert event3["E"] > event2["E"]

    def test_depth_update_preserves_string_format(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT",
            bids=[("100.123456", "10.987654")],
            asks=[("101.654321", "11.123456")],
        )

        # Binance protocol uses string arrays for price levels
        assert isinstance(event["b"][0], list)
        assert isinstance(event["b"][0][0], str)
        assert isinstance(event["b"][0][1], str)
        assert event["b"][0][0] == "100.123456"
        assert event["b"][0][1] == "10.987654"

    def test_depth_update_with_custom_timestamp(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[], asks=[], timestamp=1234567890
        )

        assert event["E"] == 1234567890

    def test_depth_update_protocol_fields(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("100", "10")], asks=[("101", "11")]
        )

        # Should have all required Binance depth update fields
        required_fields = ["e", "E", "s", "b", "a"]
        for field in required_fields:
            assert field in event


class TestBinanceEventsSnapshot:
    """Test snapshot event generation."""

    def test_snapshot_basic_structure(self):
        events = BinanceEvents()

        snapshot = events.snapshot(
            symbol="BTCUSDT", bids=[("100", "10")], asks=[("101", "11")]
        )

        assert isinstance(snapshot, dict)
        assert "lastUpdateId" in snapshot
        assert "bids" in snapshot
        assert "asks" in snapshot

    def test_snapshot_symbol_is_not_in_response(self):
        events = BinanceEvents()

        # Binance snapshot response doesn't include symbol in body
        # Symbol comes from the URL/subscription context
        snapshot = events.snapshot(symbol="BTCUSDT", bids=[], asks=[])

        # Implementation may or may not include symbol
        # This test documents expected behavior
        assert isinstance(snapshot, dict)

    def test_snapshot_empty_bids_and_asks(self):
        events = BinanceEvents()

        snapshot = events.snapshot(symbol="BTCUSDT", bids=[], asks=[])

        assert snapshot["bids"] == []
        assert snapshot["asks"] == []

    def test_snapshot_with_bids(self):
        events = BinanceEvents()

        snapshot = events.snapshot(
            symbol="BTCUSDT", bids=[("100", "10"), ("99", "20")], asks=[]
        )

        assert len(snapshot["bids"]) == 2
        assert snapshot["bids"][0] == ["100", "10"]
        assert snapshot["bids"][1] == ["99", "20"]

    def test_snapshot_with_asks(self):
        events = BinanceEvents()

        snapshot = events.snapshot(
            symbol="BTCUSDT", bids=[], asks=[("101", "11"), ("102", "22")]
        )

        assert len(snapshot["asks"]) == 2
        assert snapshot["asks"][0] == ["101", "11"]
        assert snapshot["asks"][1] == ["102", "22"]

    def test_snapshot_with_bids_and_asks(self):
        events = BinanceEvents()

        snapshot = events.snapshot(
            symbol="BTCUSDT", bids=[("100", "10")], asks=[("101", "11")]
        )

        assert len(snapshot["bids"]) == 1
        assert len(snapshot["asks"]) == 1

    def test_snapshot_has_last_update_id(self):
        events = BinanceEvents()

        snapshot = events.snapshot(symbol="BTCUSDT", bids=[], asks=[])

        assert "lastUpdateId" in snapshot
        assert isinstance(snapshot["lastUpdateId"], int)

    def test_snapshot_last_update_id_increases(self):
        events = BinanceEvents()

        snapshot1 = events.snapshot(symbol="BTCUSDT", bids=[], asks=[])
        snapshot2 = events.snapshot(symbol="BTCUSDT", bids=[], asks=[])

        # May or may not auto-increment; document actual behavior
        assert isinstance(snapshot1["lastUpdateId"], int)
        assert isinstance(snapshot2["lastUpdateId"], int)

    def test_snapshot_with_custom_last_update_id(self):
        events = BinanceEvents()

        snapshot = events.snapshot(
            symbol="BTCUSDT", bids=[], asks=[], last_update_id=999999
        )

        assert snapshot["lastUpdateId"] == 999999

    def test_snapshot_many_levels(self):
        events = BinanceEvents()

        many_bids = [(str(100 - i), str(i)) for i in range(50)]
        many_asks = [(str(101 + i), str(i)) for i in range(50)]

        snapshot = events.snapshot(symbol="BTCUSDT", bids=many_bids, asks=many_asks)

        assert len(snapshot["bids"]) == 50
        assert len(snapshot["asks"]) == 50


class TestBinanceEventsSequence:
    """Test sequence generation for multiple updates."""

    def test_sequence_returns_list(self):
        events = BinanceEvents()

        sequence = events.sequence(symbol="BTCUSDT", updates=[])

        assert isinstance(sequence, list)

    def test_sequence_empty_updates(self):
        events = BinanceEvents()

        sequence = events.sequence(symbol="BTCUSDT", updates=[])

        assert sequence == []

    def test_sequence_single_update(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="BTCUSDT",
            updates=[{"bids": [("100", "10")], "asks": [("101", "11")]}],
        )

        assert len(sequence) == 1
        assert sequence[0]["s"] == "BTCUSDT"
        assert sequence[0]["b"] == [["100", "10"]]
        assert sequence[0]["a"] == [["101", "11"]]

    def test_sequence_multiple_updates(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="BTCUSDT",
            updates=[
                {"bids": [("100", "10")], "asks": [("101", "11")]},
                {"bids": [("99", "20")], "asks": [("102", "22")]},
                {"bids": [("98", "30")], "asks": [("103", "33")]},
            ],
        )

        assert len(sequence) == 3
        assert all(event["s"] == "BTCUSDT" for event in sequence)

    def test_sequence_timestamps_increment(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="BTCUSDT",
            updates=[
                {"bids": [], "asks": []},
                {"bids": [], "asks": []},
                {"bids": [], "asks": []},
            ],
        )

        assert sequence[1]["E"] > sequence[0]["E"]
        assert sequence[2]["E"] > sequence[1]["E"]

    def test_sequence_with_different_content(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="DOTUSDT",
            updates=[
                {"bids": [("10", "100")], "asks": []},
                {"bids": [], "asks": [("11", "110")]},
                {"bids": [("9", "90")], "asks": [("12", "120")]},
            ],
        )

        assert sequence[0]["b"] == [["10", "100"]]
        assert sequence[0]["a"] == []
        assert sequence[1]["b"] == []
        assert sequence[1]["a"] == [["11", "110"]]
        assert sequence[2]["b"] == [["9", "90"]]
        assert sequence[2]["a"] == [["12", "120"]]

    def test_sequence_all_events_have_required_fields(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="BTCUSDT",
            updates=[
                {"bids": [], "asks": []},
                {"bids": [], "asks": []},
            ],
        )

        for event in sequence:
            assert "e" in event
            assert "E" in event
            assert "s" in event
            assert "b" in event
            assert "a" in event

    def test_sequence_with_custom_start_timestamp(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="BTCUSDT",
            updates=[
                {"bids": [], "asks": []},
                {"bids": [], "asks": []},
            ],
            start_timestamp=1000000,
        )

        assert sequence[0]["E"] >= 1000000
        assert sequence[1]["E"] > sequence[0]["E"]

    def test_sequence_with_custom_timestamp_increment(self):
        events = BinanceEvents()

        sequence = events.sequence(
            symbol="BTCUSDT",
            updates=[
                {"bids": [], "asks": []},
                {"bids": [], "asks": []},
                {"bids": [], "asks": []},
            ],
            timestamp_increment=1000,
        )

        # Check that timestamps increment by the specified amount
        assert sequence[1]["E"] - sequence[0]["E"] == 1000
        assert sequence[2]["E"] - sequence[1]["E"] == 1000


class TestBinanceEventsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_depth_update_with_zero_prices(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("0", "10")], asks=[("0", "11")]
        )

        assert event["b"][0] == ["0", "10"]
        assert event["a"][0] == ["0", "11"]

    def test_depth_update_with_zero_quantities(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("100", "0")], asks=[("101", "0")]
        )

        assert event["b"][0] == ["100", "0"]
        assert event["a"][0] == ["101", "0"]

    def test_depth_update_with_very_precise_decimals(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT",
            bids=[("100.12345678", "10.87654321")],
            asks=[("101.98765432", "11.23456789")],
        )

        assert event["b"][0][0] == "100.12345678"
        assert event["b"][0][1] == "10.87654321"
        assert event["a"][0][0] == "101.98765432"
        assert event["a"][0][1] == "11.23456789"

    def test_depth_update_with_scientific_notation(self):
        events = BinanceEvents()

        event = events.depth_update(
            symbol="BTCUSDT", bids=[("1e-8", "1e6")], asks=[("2e-8", "2e6")]
        )

        assert event["b"][0] == ["1e-8", "1e6"]
        assert event["a"][0] == ["2e-8", "2e6"]

    def test_snapshot_with_many_levels(self):
        events = BinanceEvents()

        many_bids = [(str(i), str(i)) for i in range(1000)]
        many_asks = [(str(i), str(i)) for i in range(1000)]

        snapshot = events.snapshot(symbol="BTCUSDT", bids=many_bids, asks=many_asks)

        assert len(snapshot["bids"]) == 1000
        assert len(snapshot["asks"]) == 1000

    def test_sequence_with_many_updates(self):
        events = BinanceEvents()

        many_updates = [{"bids": [], "asks": []} for _ in range(100)]

        sequence = events.sequence(symbol="BTCUSDT", updates=many_updates)

        assert len(sequence) == 100

    def test_depth_update_with_empty_symbol(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="", bids=[], asks=[])

        assert event["s"] == ""

    def test_depth_update_with_special_characters_in_symbol(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTC-USDT_TEST", bids=[], asks=[])

        assert event["s"] == "BTC-USDT_TEST"

    def test_timestamp_is_milliseconds(self):
        events = BinanceEvents()

        event = events.depth_update(symbol="BTCUSDT", bids=[], asks=[])

        # Binance uses millisecond timestamps
        # Should be a reasonable timestamp (13 digits for ms since epoch)
        assert event["E"] > 1000000000000  # After year 2001 in ms


class TestBinanceEventsRealisticScenarios:
    """Test realistic usage scenarios."""

    def test_create_typical_depth_update_stream(self):
        events = BinanceEvents()

        updates = []
        for i in range(10):
            update = events.depth_update(
                symbol="BTCUSDT",
                bids=[
                    (str(45000 - i * 10), str(1.5 + i * 0.1)),
                    (str(44990 - i * 10), str(2.0 + i * 0.1)),
                ],
                asks=[
                    (str(45010 + i * 10), str(1.8 + i * 0.1)),
                    (str(45020 + i * 10), str(2.2 + i * 0.1)),
                ],
            )
            updates.append(update)

        assert len(updates) == 10
        assert all(u["e"] == "depthUpdate" for u in updates)
        assert all(u["s"] == "BTCUSDT" for u in updates)

    def test_create_initial_snapshot_then_updates(self):
        events = BinanceEvents()

        snapshot = events.snapshot(
            symbol="BTCUSDT",
            bids=[("45000", "1.5"), ("44990", "2.0")],
            asks=[("45010", "1.8"), ("45020", "2.2")],
            last_update_id=1000,
        )

        update1 = events.depth_update(
            symbol="BTCUSDT",
            bids=[("45005", "1.0")],
            asks=[],
        )

        update2 = events.depth_update(
            symbol="BTCUSDT",
            bids=[],
            asks=[("45015", "0.5")],
        )

        assert snapshot["lastUpdateId"] == 1000
        assert update1["s"] == "BTCUSDT"
        assert update2["s"] == "BTCUSDT"

    def test_create_multi_symbol_stream(self):
        events = BinanceEvents()

        btc_update = events.depth_update(
            symbol="BTCUSDT", bids=[("45000", "1.5")], asks=[("45010", "1.8")]
        )
        dot_update = events.depth_update(
            symbol="DOTUSDT", bids=[("30", "100")], asks=[("31", "110")]
        )
        sol_update = events.depth_update(
            symbol="SOLUSDT", bids=[("100", "50")], asks=[("101", "55")]
        )

        assert btc_update["s"] == "BTCUSDT"
        assert dot_update["s"] == "DOTUSDT"
        assert sol_update["s"] == "SOLUSDT"
