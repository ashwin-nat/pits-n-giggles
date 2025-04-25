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
from apps.lib.f1_types import TyreSetData, PacketTyreSetsData, F1PacketType, PacketHeader, \
    ActualTyreCompound, VisualTyreCompound, SessionType23, SessionType24
from .tests_parser_base import F1TypesTest

class TestPacketTyreSetsData(F1TypesTest):
    """
    Tests for TestPacketTyreSetsData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.TYRE_SETS, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.TYRE_SETS, 24, self.m_num_players)

    def test_f1_23_random(self):
        """
        Test for F1 2023 with random data
        """

        generated_test_obj = self._generateRandomPacketTyreSetsData(self.m_header_23)
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_23, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketTyreSetsData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_24_random(self):
        """
        Test for F1 2024 with random data
        """

        generated_test_obj = self._generateRandomPacketTyreSetsData(self.m_header_24)
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketTyreSetsData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with actual data
        """

        raw_packet = b'\x0e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "car-index": 14,
            "tyre-set-data": [
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "0",
                    "visual-tyre-compound": "0",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Unknown",
                    "life-span": 0,
                    "usable-life": 0,
                    "lap-delta-time": 0,
                    "fitted": False
                }
            ],
            "fitted-index": 0
        }

        parsed_packet = PacketTyreSetsData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'\x01\x12\x10\x00\x00\x01\x12\x12\xfd\xff\x00\x13\x11\x00\x00\x01\x13\x13|\x02\x00\x12\x10\x00\x00\x02\x12\x12\xfd\xff\x00\x13\x11\x00\x00\x02\x13\x13|\x02\x00\x12\x10\x00\x00\x03\x12\x12\xfd\xff\x00\x12\x10\x00\x00\x03\x12\x12\xfd\xff\x00\x12\x10\x00\x01\x05\x12\x12\x00\x00\x01\x12\x10\x00\x01\x05\x12\x12\xfd\xff\x00\x12\x10\x00\x01\x06\x12\x12\xfd\xff\x00\x14\x12\x00\x01\x06$$\t\x06\x00\x12\x10\x00\x00\x07\x12\x12\xfd\xff\x00\x13\x11\x00\x01\x0f\x13\x13|\x02\x00\x14\x12\x00\x01\x0f$$\t\x06\x00\x07\x07\x00\x01\x00\x1b\x1b<)\x00\x07\x07\x00\x01\x00\x1b\x1b<)\x00\x07\x07\x00\x01\x00\x1b\x1b<)\x00\x07\x07\x00\x01\x00\x1b\x1b<)\x00\x08\x08\x00\x01\x00\x18\x18<)\x00\x07\x07\x00\x01\x0f\x1b\x1b<)\x00\x08\x08\x00\x01\x0f\x18\x18<)\x00\x06'
        expected_json = {
            "car-index": 1,
            "tyre-set-data": [
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Practice 1",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C2",
                    "visual-tyre-compound": "Medium",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Practice 1",
                    "life-span": 19,
                    "usable-life": 19,
                    "lap-delta-time": 636,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Practice 2",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C2",
                    "visual-tyre-compound": "Medium",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Practice 2",
                    "life-span": 19,
                    "usable-life": 19,
                    "lap-delta-time": 636,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Practice 3",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Practice 3",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Qualifying 1",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": 0,
                    "fitted": True
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Qualifying 1",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Qualifying 2",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C1",
                    "visual-tyre-compound": "Hard",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Qualifying 2",
                    "life-span": 36,
                    "usable-life": 36,
                    "lap-delta-time": 1545,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C3",
                    "visual-tyre-compound": "Soft",
                    "wear": 0,
                    "available": False,
                    "recommended-session": "Qualifying 3",
                    "life-span": 18,
                    "usable-life": 18,
                    "lap-delta-time": -3,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C2",
                    "visual-tyre-compound": "Medium",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Race",
                    "life-span": 19,
                    "usable-life": 19,
                    "lap-delta-time": 636,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "C1",
                    "visual-tyre-compound": "Hard",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Race",
                    "life-span": 36,
                    "usable-life": 36,
                    "lap-delta-time": 1545,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Inters",
                    "visual-tyre-compound": "Inters",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Unknown",
                    "life-span": 27,
                    "usable-life": 27,
                    "lap-delta-time": 10556,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Inters",
                    "visual-tyre-compound": "Inters",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Unknown",
                    "life-span": 27,
                    "usable-life": 27,
                    "lap-delta-time": 10556,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Inters",
                    "visual-tyre-compound": "Inters",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Unknown",
                    "life-span": 27,
                    "usable-life": 27,
                    "lap-delta-time": 10556,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Inters",
                    "visual-tyre-compound": "Inters",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Unknown",
                    "life-span": 27,
                    "usable-life": 27,
                    "lap-delta-time": 10556,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Wet",
                    "visual-tyre-compound": "Wet",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Unknown",
                    "life-span": 24,
                    "usable-life": 24,
                    "lap-delta-time": 10556,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Inters",
                    "visual-tyre-compound": "Inters",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Race",
                    "life-span": 27,
                    "usable-life": 27,
                    "lap-delta-time": 10556,
                    "fitted": False
                },
                {
                    "actual-tyre-compound": "Wet",
                    "visual-tyre-compound": "Wet",
                    "wear": 0,
                    "available": True,
                    "recommended-session": "Race",
                    "life-span": 24,
                    "usable-life": 24,
                    "lap-delta-time": 10556,
                    "fitted": False
                }
            ],
            "fitted-index": 6
        }


        parsed_packet = PacketTyreSetsData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def _generateRandomTyreSetData(self, header: PacketHeader) -> TyreSetData:
        """
        Generate random tyre set data

        Args:
            header (PacketHeader): The header of the packet

        Returns:
            TyreSetData: Random tyre set data
        """

        session_obj_type = SessionType23 if header.m_gameYear == 23 else SessionType24
        return TyreSetData.from_values(
            game_year=header.m_gameYear,
            actual_tyre_compound=random.choice(list(ActualTyreCompound)),
            visual_tyre_compound=random.choice(list(VisualTyreCompound)),
            wear=random.randint(0, 100),
            available=F1TypesTest.getRandomBool(),
            recommended_session=random.choice(list(session_obj_type)),
            life_span=random.randint(0, 30),
            usable_life=random.randint(0, 20),
            lap_delta_time=random.randrange(0, 10000),
            fitted=F1TypesTest.getRandomBool(),
        )

    def _generateRandomPacketTyreSetsData(self, header: PacketHeader) -> PacketTyreSetsData:
        """
        Generate random packet data
        """

        return PacketTyreSetsData.from_values(
            header=header,
            car_index=random.randint(0, self.m_num_players - 1),
            tyre_set_data=[self._generateRandomTyreSetData(header) for _ in range(PacketTyreSetsData.MAX_TYRE_SETS)],
            fitted_index=random.randrange(0, PacketTyreSetsData.MAX_TYRE_SETS)
        )


