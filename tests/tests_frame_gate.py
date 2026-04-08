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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.telemetry_manager.frame_gate import SessionFrameGate
from lib.f1_types import PacketHeader, F1PacketBase, F1PacketType
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class DummyPacket(F1PacketBase):
    """
    Minimal concrete packet for testing SessionFrameGate.
    """
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

    def test_first_packet_accepted(self) -> None:
        pkt = DummyPacket(1, 10, self.packet_types[0])
        self.assertTrue(self.gate.should_accept(pkt))
        self.assertIsNone(self.gate.last_drop_reason)

    def test_monotonic_frames(self) -> None:
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 1, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 2, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 3, self.packet_types[0])))
        self.assertIsNone(self.gate.last_drop_reason)

    def test_OUT_OF_ORDER_PKT_dropped(self) -> None:
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 10, self.packet_types[0])))
        self.assertFalse(self.gate.should_accept(DummyPacket(1, 9, self.packet_types[0])))

        reason = self.gate.last_drop_reason
        self.assertIsNotNone(reason)
        self.assertEqual(reason, self.gate._OOO_REASON)

    def test_duplicate_packet_type_same_frame_dropped(self) -> None:
        frame = 100
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertFalse(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))

        reason = self.gate.last_drop_reason
        self.assertEqual(reason, self.gate._DUP_REASON)

    def test_different_packet_types_same_frame_allowed(self) -> None:
        frame = 200

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, self.packet_types[1])))

        self.assertIsNone(self.gate.last_drop_reason)

    def test_new_frame_clears_seen_packet_types(self) -> None:
        frame = 300
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame + 1, pkt_type)))
        self.assertIsNone(self.gate.last_drop_reason)

    def test_frame_zero_resets(self) -> None:
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 50, self.packet_types[0])))
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 0, self.packet_types[0])))

        # Frame 0 is special -> duplicates allowed
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 0, self.packet_types[0])))

    def test_session_change_resets_state(self) -> None:
        frame = 400
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertTrue(self.gate.should_accept(DummyPacket(2, frame, pkt_type)))

        self.assertIsNone(self.gate.last_drop_reason)

    def test_duplicate_after_session_change_isolated(self) -> None:
        frame = 500
        pkt_type = self.packet_types[0]

        self.assertTrue(self.gate.should_accept(DummyPacket(1, frame, pkt_type)))
        self.assertTrue(self.gate.should_accept(DummyPacket(2, frame, pkt_type)))
        self.assertFalse(self.gate.should_accept(DummyPacket(2, frame, pkt_type)))

    def test_drop_reason_cleared_after_accept(self) -> None:
        self.assertTrue(self.gate.should_accept(DummyPacket(1, 10, self.packet_types[0])))
        self.assertFalse(self.gate.should_accept(DummyPacket(1, 10, self.packet_types[0])))
        self.assertIsNotNone(self.gate.last_drop_reason)

        self.assertTrue(self.gate.should_accept(DummyPacket(1, 11, self.packet_types[0])))
        self.assertIsNone(self.gate.last_drop_reason)

    def test_disabled_mode_always_accepts(self) -> None:
        gate = SessionFrameGate(enabled=False)

        pkt_type = self.packet_types[0]

        # Send chaotic sequence
        self.assertTrue(gate.should_accept(DummyPacket(1, 10, pkt_type)))
        self.assertTrue(gate.should_accept(DummyPacket(1, 9, pkt_type)))   # backward
        self.assertTrue(gate.should_accept(DummyPacket(1, 9, pkt_type)))   # duplicate
        self.assertTrue(gate.should_accept(DummyPacket(2, 5, pkt_type)))   # session change
        self.assertTrue(gate.should_accept(DummyPacket(2, 0, pkt_type)))   # frame 0

        self.assertIsNone(gate.last_drop_reason)
