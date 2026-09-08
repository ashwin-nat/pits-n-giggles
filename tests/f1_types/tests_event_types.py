# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import random
import pytest

from lib.f1_types import (F1PacketType, PacketEventData, PacketHeader,
                          UnsupportedValueError)
from lib.telemetry_manager.factory import PacketParserFactory
from tests.f1_types.tests_parser_base import F1TypesTest

Collision = PacketEventData.Collision
CollisionSeverity = PacketEventData.Collision.CollisionSeverity


# -------------------------------------- HELPERS -----------------------------------------------------------------------

def _make_event_header(game_year: int) -> PacketHeader:
    num_players = 24 if game_year >= 2026 else 22
    return F1TypesTest.getRandomHeader(F1PacketType.EVENT, game_year, num_players)


def _roundtrip(header: PacketHeader, collision: Collision) -> PacketEventData:
    """Serialize a Collision event to bytes and parse it back."""
    generated = PacketEventData.from_values(header, PacketEventData.EventPacketType.COLLISION, collision)
    raw = generated.to_bytes(include_header=True)
    parsed_header = PacketHeader(raw[:PacketHeader.PACKET_LEN])
    return PacketEventData(parsed_header, raw[PacketHeader.PACKET_LEN:])


# -------------------------------------- COLLISION (COLL) --------------------------------------------------------------

def test_collision_pre2026_roundtrip():
    """Collision event round-trip for pre-2026 format — no severity field."""
    header = _make_event_header(game_year=25)
    v1 = random.randint(0, 21)
    v2 = random.randint(0, 21)

    collision = Collision.from_values(v1, v2, packet_format=2025)
    parsed = _roundtrip(header, collision)

    assert parsed.m_eventCode == PacketEventData.EventPacketType.COLLISION
    assert parsed.mEventDetails.m_vehicle_1_index == v1
    assert parsed.mEventDetails.m_vehicle_2_index == v2
    assert parsed.mEventDetails.m_severity is None
    assert parsed.toJSON() == {
        "event-string-code": "COLL",
        "event-details": {
            "vehicle-1-index": v1,
            "vehicle-2-index": v2,
            "severity": None,
        },
    }
    assert not hasattr(parsed, "__dict__")


@pytest.mark.parametrize("severity", list(CollisionSeverity))
def test_collision_2026_roundtrip(severity: CollisionSeverity):
    """Collision event round-trip for F1 2026 — severity field included."""
    header = _make_event_header(game_year=26)
    v1 = random.randint(0, 23)
    v2 = random.randint(0, 23)

    collision = Collision.from_values(v1, v2, severity=severity, packet_format=2026)
    parsed = _roundtrip(header, collision)

    assert parsed.m_eventCode == PacketEventData.EventPacketType.COLLISION
    assert parsed.mEventDetails.m_vehicle_1_index == v1
    assert parsed.mEventDetails.m_vehicle_2_index == v2
    assert parsed.mEventDetails.m_severity == severity
    assert parsed.toJSON() == {
        "event-string-code": "COLL",
        "event-details": {
            "vehicle-1-index": v1,
            "vehicle-2-index": v2,
            "severity": str(severity),
        },
    }
    assert not hasattr(parsed, "__dict__")


# -------------------------------------- UNKNOWN EVENT CODES -----------------------------------------------------------

def _parse_event_code(code: bytes, game_year: int = 25) -> PacketEventData:
    """Build a raw event packet carrying an arbitrary 4-byte event code and parse it."""
    header = _make_event_header(game_year)
    return PacketEventData(header, code + b"\x00" * 32)


@pytest.mark.parametrize("code", [b"ZZZZ", b"XYZW", b"1234"])
def test_unknown_event_code_is_rejected(code):
    # A PacketEventData is only meaningful if it identifies an event. An undeclared code
    # leaves nothing to act on, so the object must not be constructed at all
    with pytest.raises(UnsupportedValueError):
        _parse_event_code(code)


@pytest.mark.parametrize("code", [b"ZZZZ", b"XYZW"])
def test_unknown_event_code_is_named_in_the_error(code):
    # The offending code has to reach the log, otherwise a newly added game event is
    # indistinguishable from silence
    with pytest.raises(UnsupportedValueError) as exc_info:
        _parse_event_code(code)

    assert exc_info.value.m_value == code.decode("ascii")
    assert code.decode("ascii") in str(exc_info.value)


def test_non_ascii_event_code_is_rejected():
    # Decoded with errors='replace', so a corrupt code arrives as an ordinary unknown code
    # and is rejected the same way, rather than as a UnicodeDecodeError
    with pytest.raises(UnsupportedValueError):
        _parse_event_code(b"\xff\xfe\xfd\xfc")


def test_unknown_event_code_does_not_pass_the_parser_factory():
    # The factory has to swallow it: an exception escaping here would kill the receive loop
    logger = logging.getLogger("tests_event_types")
    logger.addHandler(logging.NullHandler())
    factory = PacketParserFactory(set(F1PacketType), logger)

    header = _make_event_header(game_year=25)
    raw = header.to_bytes() + b"XYZW" + b"\x00" * 32

    assert factory.parse(raw) is None
    assert "XYZW" in factory.last_failure_reason


def test_known_event_codes_are_unaffected():
    parsed = _parse_event_code(b"SSTA")

    assert parsed.m_eventCode == PacketEventData.EventPacketType.SESSION_STARTED
    assert not parsed.m_eventCode.is_unknown()


# -------------------------------------- PARTIAL AERO MODE ENABLED -----------------------------------------------------

PartialAeroModeEnabled = PacketEventData.PartialAeroModeEnabled
PartialAeroModeReason = PacketEventData.PartialAeroModeEnabled.Reason


def _roundtrip_partial_aero_mode(header: PacketHeader, reason_byte: int) -> PacketEventData:
    """Serialize a PartialAeroModeEnabled event to bytes and parse it back."""
    details = PartialAeroModeEnabled(bytes([reason_byte]), header.m_packetFormat)
    generated = PacketEventData.from_values(
        header, PacketEventData.EventPacketType.PARTIAL_AERO_MODE_ENABLED, details)
    raw = generated.to_bytes(include_header=True)
    parsed_header = PacketHeader(raw[:PacketHeader.PACKET_LEN])
    return PacketEventData(parsed_header, raw[PacketHeader.PACKET_LEN:])


@pytest.mark.parametrize("reason", [
    PartialAeroModeReason.WET_TRACK,
    PartialAeroModeReason.SAFETY_CAR_DEPLOYED,
    PartialAeroModeReason.RED_FLAG,
])
def test_partial_aero_mode_enabled_roundtrip(reason):
    parsed = _roundtrip_partial_aero_mode(_make_event_header(game_year=25), reason.value)

    assert parsed.m_eventCode == PacketEventData.EventPacketType.PARTIAL_AERO_MODE_ENABLED
    assert parsed.mEventDetails.m_reason == reason
    assert not parsed.mEventDetails.m_reason.is_unknown()
    assert parsed.toJSON() == {
        "event-string-code": "PMEN",
        "event-details": {"reason": str(reason)},
    }
    assert not hasattr(parsed, "__dict__")


@pytest.mark.parametrize("reason_byte", [3, 9, 200])
def test_partial_aero_mode_enabled_unknown_reason_roundtrips(reason_byte):
    # An undeclared reason must survive the round trip as the byte that arrived, not
    # collapse onto the UNKNOWN sentinel's own value
    parsed = _roundtrip_partial_aero_mode(_make_event_header(game_year=25), reason_byte)

    assert parsed.mEventDetails.m_reason == PartialAeroModeReason.UNKNOWN
    assert parsed.mEventDetails.m_reason.is_unknown()
    assert parsed.mEventDetails.m_reason.raw_value == reason_byte
    assert parsed.mEventDetails.to_bytes(2025) == bytes([reason_byte])


@pytest.mark.parametrize("code, event_type", [
    ("PMDI", PacketEventData.EventPacketType.PARTIAL_AERO_MODE_DISABLED),
    ("OVEN", PacketEventData.EventPacketType.OVERTAKE_MODE_ENABLED),
    ("OVDI", PacketEventData.EventPacketType.OVERTAKE_MODE_DISABLED),
])
def test_new_no_payload_events_parse(code, event_type):
    header = _make_event_header(game_year=25)
    parsed = PacketEventData(header, code.encode("ascii") + b"\x00" * 32)

    assert parsed.m_eventCode == event_type
    assert not parsed.m_eventCode.is_unknown()
    assert parsed.mEventDetails is None
    assert parsed.toJSON() == {"event-string-code": code, "event-details": None}
