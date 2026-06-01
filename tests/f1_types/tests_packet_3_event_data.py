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

import random
from lib.f1_types import PacketEventData, F1PacketType
from .tests_parser_base import F1TypesTest

class TestPacketEventData(F1TypesTest):
    """
    Tests for PacketEventData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = random.randint(1, 22)

    def test_f1_24_session_started(self):
        """
        Test for F1 2024 with an actual game packet. Session Started event
        """

        random_header = F1TypesTest.getRandomHeader(F1PacketType.EVENT, 24, self.m_num_players)
        raw_packet = b'SSTA\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "event-string-code": "SSTA",
            "event-details": None
        }

        parsed_packet = PacketEventData(random_header, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_24_fastest_lap(self):
        """
        Test for F1 2024 with an actual game packet. Fastest Lap event
        """

        random_header = F1TypesTest.getRandomHeader(F1PacketType.EVENT, 24, self.m_num_players)
        raw_packet = b'FTLP\x04\x11X\xdcB\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "event-string-code": "FTLP",
            "event-details": {
                "vehicle-idx": 4,
                "lap-time": 110.17200469970703
            }
        }

        parsed_packet = PacketEventData(random_header, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_25_fastest_lap(self):
        """
        Test for F1 2025 with an actual game packet. Fastest Lap event
        """

        random_header = F1TypesTest.getRandomHeader(F1PacketType.EVENT, 25, self.m_num_players)
        raw_packet = b'FTLP\x07\x14.\x89B\x00\x00\x00\x02\x1amP'
        expected_json = {"event-string-code": "FTLP", "event-details": {"vehicle-idx": 7, "lap-time": 68.58999633789062}}

        parsed_packet = PacketEventData(random_header, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_24_collision_random(self):
        """Test for F1 2024 Collision event (no severity field)."""

        from lib.f1_types import PacketHeader
        v1 = random.randint(0, 21)
        v2 = random.randint(0, 21)
        header = F1TypesTest.getRandomHeader(F1PacketType.EVENT, 24, self.m_num_players)
        collision = PacketEventData.Collision.from_values(v1, v2, packet_format=2024)
        generated = PacketEventData.from_values(header, PacketEventData.EventPacketType.COLLISION, collision)
        serialised = generated.to_bytes(include_header=True)
        parsed_header = PacketHeader(serialised[:PacketHeader.PACKET_LEN])
        parsed = PacketEventData(parsed_header, serialised[PacketHeader.PACKET_LEN:])
        self.assertEqual(generated, parsed)
        expected_json = {
            "event-string-code": "COLL",
            "event-details": {
                "vehicle-1-index": v1,
                "vehicle-2-index": v2,
                "severity": None,
            }
        }
        self.jsonComparisionUtil(expected_json, parsed.toJSON())
        self.assertFalse(hasattr(parsed, '__dict__'))

    def test_f1_26_collision_random(self):
        """Test for F1 2026 Collision event (includes severity field)."""

        from lib.f1_types import PacketHeader
        v1 = random.randint(0, 23)
        v2 = random.randint(0, 23)
        severity = PacketEventData.Collision.CollisionSeverity(random.randint(0, 2))
        header = F1TypesTest.getRandomHeader(F1PacketType.EVENT, 26, self.m_num_players)
        collision = PacketEventData.Collision.from_values(v1, v2, severity=severity, packet_format=2026)
        generated = PacketEventData.from_values(header, PacketEventData.EventPacketType.COLLISION, collision)
        serialised = generated.to_bytes(include_header=True)
        parsed_header = PacketHeader(serialised[:PacketHeader.PACKET_LEN])
        parsed = PacketEventData(parsed_header, serialised[PacketHeader.PACKET_LEN:])
        self.assertEqual(generated, parsed)
        expected_json = {
            "event-string-code": "COLL",
            "event-details": {
                "vehicle-1-index": v1,
                "vehicle-2-index": v2,
                "severity": str(severity),
            }
        }
        self.jsonComparisionUtil(expected_json, parsed.toJSON())
        self.assertFalse(hasattr(parsed, '__dict__'))

    def test_f1_26_collision_actual(self):
        """Test for F1 2026 Collision event with an actual game packet."""
        # F126-CAPTURE: PKT3
        self.skipTest("awaiting 2026 capture")
        # --- fill in once captured, then remove skipTest above ---
        # Capture point: lib/telemetry_manager/factory.py — gate on format==2026 and packetId==3, event code "COLL"
        # raw_packet includes the 4-byte "COLL" code followed by the 3-byte payload
        # raw_packet = b'COLL\xNN\xNN\xNN'
        # expected_json = {
        #     "event-string-code": "COLL",
        #     "event-details": {
        #         "vehicle-1-index": 0,
        #         "vehicle-2-index": 0,
        #         "severity": "LOW",  # LOW / MEDIUM / HIGH
        #     }
        # }
        # random_header = F1TypesTest.getRandomHeader(F1PacketType.EVENT, 26, self.m_num_players)
        # parsed_packet = PacketEventData(random_header, raw_packet)
        # parsed_json = parsed_packet.toJSON()
        # self.jsonComparisionUtil(expected_json, parsed_json)
        # self.assertFalse(hasattr(parsed_packet, '__dict__'))
