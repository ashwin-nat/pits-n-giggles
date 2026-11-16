# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
# pylint: skip-file

import os
from unittest.mock import patch
import sys

import allure
import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.telemetry_manager.frame_gate import SessionFrameGate
from lib.f1_types import PacketHeader, F1PacketBase, F1PacketType
from tests_base import F1TelemetryUnitTestsBase

pytestmark = [allure.epic("Telemetry manager"), allure.feature("Frame gate")]

# ----------------------------------------------------------------------------------------------------------------------

class DummyPacket(F1PacketBase):
    """
    Minimal concrete packet for testing SessionFrameGate.
    """
    ABSTRACT = True     # Takes its packet type per instance, so it registers as no parser
    __slots__ = ()

    def __init__(self, session_uid: int, frame_id: int, packet_type: F1PacketType):
        header = PacketHeader.from_values(
            packet_format=2025,
            game_year=25,
            game_major_version=1,
            game_minor_version=0,
            packet_version=1,
            packet_type=packet_type,
            session_uid=session_uid,
            session_time=0.0,
            frame_identifier=frame_id,
            overall_frame_identifier=frame_id,
            player_car_index=0,
            secondary_player_car_index=255,
        )
        super().__init__(header)

class TestSessionFrameGate(F1TelemetryUnitTestsBase):

    def setUp(self) -> None:
        self.gate = SessionFrameGate()
        self.packet_types = list(F1PacketType)

    @allure.story("Ordering")
    @allure.title("The first packet is accepted")
    def test_first_packet_accepted(self) -> None:
        """One MOTION packet on frame 10, the gate's first.

        Expected: accepted, with no drop reason."""
        pkt = DummyPacket(1, 10, self.packet_types[0])
        self.assertTrue(self.gate.should_accept(pkt))
        self.assertIsNone(self.gate.last_drop_reason)

    @allure.story("Ordering")
    @allure.title("Packets on rising frames are all accepted")
    def test_monotonic_frames(self) -> None:
        """MOTION on frames 1, 2 and 3.

        Expected: all three accepted, with no drop reason."""
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 1, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 2, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 3, self.packet_types[0])))
        self.assertIsNone(self.gate.last_drop_reason)

    @allure.story("Ordering")
    @allure.title("A packet on an earlier frame is dropped as out of order")
    def test_OUT_OF_ORDER_PKT_dropped(self) -> None:
        """MOTION on frame 10, then on frame 9.

        Expected: the second is dropped, with OUT_OF_ORDER_PKT as the reason."""
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 10, self.packet_types[0])))
        self.assertFalse(self.gate.should_accept(DummyPacket(1, 9, self.packet_types[0])))

        reason = self.gate.last_drop_reason
        self.assertIsNotNone(reason)
        self.assertEqual(reason, self.gate._OOO_REASON)

    @allure.story("One of each type per frame")
    @allure.title("A second packet of the same type on one frame is dropped")
    def test_duplicate_packet_type_same_frame_dropped(self) -> None:
        """Two MOTION packets on frame 100.

        Expected: the second is dropped, with DUPLICATE_PACKET_TYPE as the reason."""
        frame = 100
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertFalse(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))

        reason = self.gate.last_drop_reason
        self.assertEqual(reason, self.gate._DUP_REASON)

    @allure.story("One of each type per frame")
    @allure.title("Different packet types on one frame are all accepted")
    def test_different_packet_types_same_frame_allowed(self) -> None:
        """MOTION, then SESSION, both on frame 200.

        Expected: both accepted, with no drop reason."""
        frame = 200

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, self.packet_types[1])))

        self.assertIsNone(self.gate.last_drop_reason)

    @allure.story("One of each type per frame")
    @allure.title("A new frame accepts a type the last frame already had")
    def test_new_frame_clears_seen_packet_types(self) -> None:
        """MOTION on frame 300, then MOTION on frame 301.

        Expected: both accepted, with no drop reason."""
        frame = 300
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame + 1, pkt_type)))
        self.assertIsNone(self.gate.last_drop_reason)

    @allure.story("Resets")
    @allure.title("Frame 0 resets the gate and accepts duplicates")
    def test_frame_zero_resets(self) -> None:
        """MOTION on frame 50, then two MOTION packets on frame 0.

        Expected: all accepted. Frame 0 isn't held to ordering or one of each type."""
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 50, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 0, self.packet_types[0])))

        # Frame 0 is special -> duplicates allowed
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 0, self.packet_types[0])))

    @allure.story("Resets")
    @allure.title("A new session UID starts the gate afresh")
    def test_session_change_resets_state(self) -> None:
        """MOTION on frame 400 in session 1, then MOTION on frame 400 in session 2.

        Expected: both accepted, with no drop reason."""
        frame = 400
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertTrue(self.gate.should_accept(DummyPacket(2, frame, pkt_type)))

        self.assertIsNone(self.gate.last_drop_reason)

    @allure.story("Resets")
    @allure.title("After a session change, duplicates count within the new session")
    def test_duplicate_after_session_change_isolated(self) -> None:
        """MOTION on frame 500 in session 1, then twice on frame 500 in session 2.

        Expected: the first two accepted, the third dropped as a duplicate within session 2."""
        frame = 500
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertTrue(self.gate.should_accept(DummyPacket(2, frame, pkt_type)))
        self.assertFalse(self.gate.should_accept(DummyPacket(2, frame, pkt_type)))

    @allure.story("Drop reason")
    @allure.title("The drop reason clears on the next accepted packet")
    def test_drop_reason_cleared_after_accept(self) -> None:
        """MOTION twice on frame 10, then on frame 11.

        Expected: the duplicate sets a drop reason, and the frame 11 packet clears it."""
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 10, self.packet_types[0])))
        self.assertFalse(self.gate.should_accept(DummyPacket(1, 10, self.packet_types[0])))
        self.assertIsNotNone(self.gate.last_drop_reason)

        self.assertTrue(self.gate.should_accept(DummyPacket(1, 11, self.packet_types[0])))
        self.assertIsNone(self.gate.last_drop_reason)

    @allure.story("Disabled")
    @allure.title("A disabled gate accepts everything")
    def test_disabled_mode_always_accepts(self) -> None:
        """Gate disabled. MOTION on frame 10, then 9 twice, then frame 5 in a new session, then frame 0.

        Expected: all accepted, with no drop reason."""
        gate = SessionFrameGate(enabled=False)

        pkt_type = self.packet_types[0]

        # Send chaotic sequence
        self.assertTrue(gate.should_accept(DummyPacket(1, 10, pkt_type)))
        self.assertTrue(gate.should_accept(DummyPacket(1, 9, pkt_type)))   # backward
        self.assertTrue(gate.should_accept(DummyPacket(1, 9, pkt_type)))   # duplicate
        self.assertTrue(gate.should_accept(DummyPacket(2, 5, pkt_type)))   # session change
        self.assertTrue(gate.should_accept(DummyPacket(2, 0, pkt_type)))   # frame 0

        self.assertIsNone(gate.last_drop_reason)

    @allure.story("Ordering")
    @allure.title("A flashback's rewound frame ID isn't dropped as out of order")
    def test_flashback_does_not_trigger_backward_drop(self) -> None:
        """MOTION on frames 1000 and 1001. Then a flashback: the frame ID goes back to 900, and the overall frame ID
        carries on to 1002, then 1003.

        Expected: all accepted. The gate keys off the overall frame ID, which a flashback doesn't rewind."""

        pkt_type = self.packet_types[0]

        # Normal progression
        pkt1 = DummyPacket(1, frame_id=1000, packet_type=pkt_type)
        pkt1.m_header.m_overallFrameIdentifier = 1000

        pkt2 = DummyPacket(1, frame_id=1001, packet_type=pkt_type)
        pkt2.m_header.m_overallFrameIdentifier = 1001

        self.assertTrue(self.gate.should_accept(pkt1))
        self.assertTrue(self.gate.should_accept(pkt2))

        # Flashback occurs: frame rewinds but overall frame increases
        pkt_flashback = DummyPacket(1, frame_id=900, packet_type=pkt_type)
        pkt_flashback.m_header.m_overallFrameIdentifier = 1002

        # Must be accepted
        self.assertTrue(self.gate.should_accept(pkt_flashback))

        # Same simulation frame but new overall frame -> still accepted
        pkt_next = DummyPacket(1, frame_id=900, packet_type=pkt_type)
        pkt_next.m_header.m_overallFrameIdentifier = 1003

        self.assertTrue(self.gate.should_accept(pkt_next))

# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Bursts on one frame")
@allure.title("22 {pkt_type} packets on one frame are all accepted")
@pytest.mark.parametrize("pkt_type", [F1PacketType.EVENT, F1PacketType.SESSION_HISTORY])
def test_multi_per_frame_types_allow_several_in_one_frame(pkt_type):
    """22 packets of the type on frame 600, as in a burst of BUTN events then FLBK, or session history for every car.

    Expected: all accepted, with no drop reason."""
    gate = SessionFrameGate()

    assert all(gate.should_accept(DummyPacket(1, 600, pkt_type)) for _ in range(22))
    assert gate.last_drop_reason is None


@allure.story("Bursts on one frame")
@allure.title("{pkt_type} is still dropped when out of order")
@pytest.mark.parametrize("pkt_type", [F1PacketType.EVENT, F1PacketType.SESSION_HISTORY])
def test_multi_per_frame_types_still_dropped_out_of_order(pkt_type):
    """A packet of the type on frame 700, then on frame 699.

    Expected: the second is dropped, with OUT_OF_ORDER_PKT as the reason. Only one of each type is relaxed."""
    gate = SessionFrameGate()

    assert gate.should_accept(DummyPacket(1, 700, pkt_type))
    assert not gate.should_accept(DummyPacket(1, 699, pkt_type))
    assert gate.last_drop_reason == SessionFrameGate._OOO_REASON


@allure.story("Bursts on one frame")
@allure.title("Other types stay one per frame alongside an EVENT burst")
def test_other_types_still_unique_per_frame_alongside_events():
    """On frame 800: LAP_DATA, two EVENTs, then LAP_DATA again.

    Expected: the EVENTs are accepted, and the second LAP_DATA is dropped as a duplicate."""
    gate = SessionFrameGate()

    assert gate.should_accept(DummyPacket(1, 800, F1PacketType.LAP_DATA))
    assert gate.should_accept(DummyPacket(1, 800, F1PacketType.EVENT))
    assert gate.should_accept(DummyPacket(1, 800, F1PacketType.EVENT))
    assert not gate.should_accept(DummyPacket(1, 800, F1PacketType.LAP_DATA))
    assert gate.last_drop_reason == SessionFrameGate._DUP_REASON
