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

import random
import pytest

from lib.f1_types import PacketEventData, PacketHeader, F1PacketType
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
