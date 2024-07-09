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
from lib.f1_types import PacketTimeTrialData, TimeTrialDataSet, F1PacketType, PacketHeader, TeamID24, \
    GearboxAssistMode, TractionControlAssistMode
from .tests_parser_base import F1TypesTest

class TestPacketTimeTrialData(F1TypesTest):
    """
    Tests for TestPacketTimeTrialData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.TIME_TRIAL, 24, self.m_num_players)

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x00\x01\x01\x04\xfbm\x01\x00\xec^\x00\x00\xd0m\x00\x00>\xa1\x00\x00\x00\x00\x00\x01\x01\x01\x04\x00ql\x01\x00<`\x00\x00\x96n\x00\x00\x9e\x9d\x00\x00\x01\x00\x01\x00\x00\x01'
        expected_json = {
        "player-session-best-data-set": {
            "car-index": 0,
            "team": "Red Bull Racing",
            "lap-time-ms": 0,
            "lap-time-str": "00.000",
            "sector-1-time-ms": 0,
            "sector-1-time-str": "00.000",
            "sector-2-time-in-ms": 0,
            "sector-2-time-str": "00.000",
            "sector3-time-in-ms": 0,
            "sector-3-time-str": "00.000",
            "traction-control": "MEDIUM",
            "gearbox-assist": "0",
            "anti-lock-brakes": False,
            "equal-car-performance": True,
            "custom-setup": False,
            "is-valid": True
        },
        "personal-best-data-set": {
            "car-index": 1,
            "team": "Aston Martin",
            "lap-time-ms": 93691,
            "lap-time-str": "01:33.691",
            "sector-1-time-ms": 24300,
            "sector-1-time-str": "24.300",
            "sector-2-time-in-ms": 28112,
            "sector-2-time-str": "28.112",
            "sector3-time-in-ms": 41278,
            "sector-3-time-str": "41.278",
            "traction-control": "OFF",
            "gearbox-assist": "0",
            "anti-lock-brakes": False,
            "equal-car-performance": True,
            "custom-setup": True,
            "is-valid": True
        },
        "rival-session-best-data-set": {
            "car-index": 4,
            "team": "Mercedes",
            "lap-time-ms": 93297,
            "lap-time-str": "01:33.297",
            "sector-1-time-ms": 24636,
            "sector-1-time-str": "24.636",
            "sector-2-time-in-ms": 28310,
            "sector-2-time-str": "28.310",
            "sector3-time-in-ms": 40350,
            "sector-3-time-str": "40.350",
            "traction-control": "MEDIUM",
            "gearbox-assist": "0",
            "anti-lock-brakes": True,
            "equal-car-performance": False,
            "custom-setup": False,
            "is-valid": True
        }
    }

        parsed_packet = PacketTimeTrialData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.assertEqual(expected_json, parsed_json)

    def test_f1_24_random(self):
        """
        Test for F1 2024 with a random game packet
        """

        generated_test_obj = self._generateRandomPacketTimeTrialData(self.m_header_24)
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketTimeTrialData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.assertEqual(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def _generateRandomTimeTrialDataSet(self, index: int) -> TimeTrialDataSet:
        """
        Generates a random TimeTrialDataSet

        Args:
            index (int): The index of the car

        Returns:
            TimeTrialDataSet: A random TimeTrialDataSet
        """

        s1_time_ms = random.randrange(0, 60000)
        s2_time_ms = random.randrange(0, 60000)
        s3_time_ms = random.randrange(0, 60000)
        return TimeTrialDataSet.from_values(
            car_index=index,
            team_id=random.choice(list(TeamID24)),
            lap_time_in_ms=(s1_time_ms + s2_time_ms + s3_time_ms),
            sector1_time_in_ms=s1_time_ms,
            sector2_time_in_ms=s2_time_ms,
            sector3_time_in_ms=s3_time_ms,
            traction_control=random.choice(list(TractionControlAssistMode)),
            gearbox_assist=random.choice(list(GearboxAssistMode)),
            anti_lock_brakes=F1TypesTest.getRandomBool(),
            equal_car_performance=F1TypesTest.getRandomBool(),
            custom_setup=F1TypesTest.getRandomBool(),
            is_valid=F1TypesTest.getRandomBool()
        )

    def _generateRandomPacketTimeTrialData(self, header: PacketHeader) -> PacketTimeTrialData:
        """
        Generates a random PacketTimeTrialData object

        Args:
            header (PacketHeader): The header of the packet

        Returns:
            PacketTimeTrialData: A random PacketTimeTrialData object
        """

        return PacketTimeTrialData.from_values(
            header=header,
            player_session_best_data_set=self._generateRandomTimeTrialDataSet(0),
            personal_best_data_set=self._generateRandomTimeTrialDataSet(1),
            rival_session_best_data_set=self._generateRandomTimeTrialDataSet(2)
        )