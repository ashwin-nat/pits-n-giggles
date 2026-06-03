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
from lib.f1_types import CarTelemetry2Data, PacketCarTelemetry2Data, F1PacketType, PacketHeader
from .tests_parser_base import F1TypesTest


class TestPacketCarTelemetry2Data(F1TypesTest):
    """Tests for PacketCarTelemetry2Data (F1 2026 only)."""

    def setUp(self) -> None:
        self.m_num_players = 24
        self.m_header_26 = F1TypesTest.getRandomHeader(F1PacketType.CAR_TELEMETRY_2, 26, self.m_num_players)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generateRandomCarTelemetry2Data() -> CarTelemetry2Data:
        return CarTelemetry2Data.from_values(
            active_aero_mode=random.randint(0, 1),
            active_aero_available=random.randint(0, 1),
            active_aero_activation_distance=random.randint(0, 65535),
            overtake_available=random.randint(0, 1),
            overtake_active=random.randint(0, 1),
            overtake_activation_distance=random.randint(0, 65535),
            regulations_2026=random.randint(0, 1),
            driving_wrong_way=random.randint(0, 1),
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_f1_26_random(self):
        """Test F1 2026 with a randomly generated packet (roundtrip)."""

        generated = PacketCarTelemetry2Data.from_values(
            self.m_header_26,
            [self._generateRandomCarTelemetry2Data() for _ in range(self.m_num_players)],
        )
        serialised = generated.to_bytes()
        header_bytes = serialised[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_26, parsed_header)
        payload_bytes = serialised[PacketHeader.PACKET_LEN:]
        parsed = PacketCarTelemetry2Data(parsed_header, payload_bytes)
        self.assertEqual(generated, parsed)
        self.jsonComparisionUtil(generated.toJSON(), parsed.toJSON())
        self.assertFalse(hasattr(parsed, '__dict__'))

    def test_f1_26_actual(self):
        """Test for F1 2026 with an actual game packet."""
        # F126-CAPTURE: PKT16
        self.skipTest("awaiting 2026 capture")
        # --- fill in once captured, then remove skipTest above ---
        # Capture point: lib/telemetry_manager/factory.py — gate on format==2026 and packetId==16
        # raw_packet contains the payload bytes only (header already stripped)
        raw_packet = b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xca\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {'car-telemetry-2-data': [{'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': True, 'overtake-active': True, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'STRAIGHT_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': True, 'overtake-active': True, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': True, 'overtake-active': True, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 202, 'overtake-available': True, 'overtake-active': True, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'STRAIGHT_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': True, 'overtake-active': True, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': True, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': True, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': False, 'driving-wrong-way': False}, {'active-aero-mode': 'CORNER_MODE', 'active-aero-available': False, 'active-aero-activation-distance': 0, 'overtake-available': False, 'overtake-active': False, 'overtake-activation-distance': 0, '2026-regulations': False, 'driving-wrong-way': False}]}
        parsed_packet = PacketCarTelemetry2Data(self.m_header_26, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))
