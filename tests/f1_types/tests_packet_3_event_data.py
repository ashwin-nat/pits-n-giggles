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

