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
from typing import Optional

from lib.f1_types import (F1PacketType, Nationality, PacketHeader,
                          PacketParticipantsData, ParticipantData, Platform,
                          TeamID23, TeamID24, TeamID25, TelemetrySetting)

from .tests_parser_base import F1TypesTest


class TestPacketParticipantsData(F1TypesTest):
    """
    Tests for TestPacketParticipantsData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = random.randint(1, 22)
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.PARTICIPANTS, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.PARTICIPANTS, 24, self.m_num_players)

    def test_f1_24_random(self):
        """
        Test for F1 2024 with an randomly generated packet
        """

        random_participants = [self._getRandomParticipantData(self.m_header_24) for _ in range(self.m_num_players)]

        generated_test_obj = PacketParticipantsData.from_values(
            self.m_header_24, self.m_num_players, random_participants)
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketParticipantsData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_random(self):
        """
        Test for F1 2023 with an randomly generated packet
        """

        random_participants = [self._getRandomParticipantData(self.m_header_23) for _ in range(self.m_num_players)]

        generated_test_obj = PacketParticipantsData.from_values(
            self.m_header_23, self.m_num_players, random_participants)
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_23, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketParticipantsData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'\x14\x01\t\xff\x02\x00!\x16VERSTAPPEN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x016\xff\x08\x00\x04\nNORRIS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x00\xff\x01\x007MSAINZ\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x03\xff\x04\x00\x0eMALONSO\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x0b\xff\x07\x00\x14\x15MAGNUSSEN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x13\xff\x04\x00\x12\rSTROLL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x84\xff\x03\x00\x02\x01SARGEANT\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\n\xff\x07\x00\x1b\x1dHULKENBERG\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01^\xff\x06\x00\x16+TSUNODA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01:\xff\x01\x00\x105LECLERC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x0f\xff\t\x00M\x1bBOTTAS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x02\xff\x06\x00\x03\x03RICCIARDO\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x07\xff\x00\x00,\nHAMILTON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x012\xff\x00\x00?\nRUSSELL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01p\xff\x08\x00Q\x03PIASTRI\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01P\xff\t\x00\x18\x0fZHOU\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x0e\xff\x02\x00\x0b4P\xc3\x89REZ\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01\x11\xff\x05\x00\x1f\x1cOCON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x01;\xff\x05\x00\n\x1cGASLY\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\x00>\xff\x03\x00\x17PALBON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x01\x00\xff\xff\xff\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "num-active-cars": 20,
            "participants": [
                {
                    "ai-controlled": True,
                    "driver-id": 9,
                    "network-id": 255,
                    "team-id": "Red Bull Racing",
                    "my-team": False,
                    "race-number": 33,
                    "nationality": "Dutch",
                    "name": "VERSTAPPEN",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 54,
                    "network-id": 255,
                    "team-id": "McLaren",
                    "my-team": False,
                    "race-number": 4,
                    "nationality": "British",
                    "name": "NORRIS",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 0,
                    "network-id": 255,
                    "team-id": "Ferrari",
                    "my-team": False,
                    "race-number": 55,
                    "nationality": "Spanish",
                    "name": "SAINZ",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 3,
                    "network-id": 255,
                    "team-id": "Aston Martin",
                    "my-team": False,
                    "race-number": 14,
                    "nationality": "Spanish",
                    "name": "ALONSO",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 11,
                    "network-id": 255,
                    "team-id": "Haas",
                    "my-team": False,
                    "race-number": 20,
                    "nationality": "Danish",
                    "name": "MAGNUSSEN",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 19,
                    "network-id": 255,
                    "team-id": "Aston Martin",
                    "my-team": False,
                    "race-number": 18,
                    "nationality": "Canadian",
                    "name": "STROLL",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 132,
                    "network-id": 255,
                    "team-id": "Williams",
                    "my-team": False,
                    "race-number": 2,
                    "nationality": "American",
                    "name": "SARGEANT",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 10,
                    "network-id": 255,
                    "team-id": "Haas",
                    "my-team": False,
                    "race-number": 27,
                    "nationality": "German",
                    "name": "HULKENBERG",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 94,
                    "network-id": 255,
                    "team-id": "VCARB",
                    "my-team": False,
                    "race-number": 22,
                    "nationality": "Japanese",
                    "name": "TSUNODA",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 58,
                    "network-id": 255,
                    "team-id": "Ferrari",
                    "my-team": False,
                    "race-number": 16,
                    "nationality": "Monegasque",
                    "name": "LECLERC",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 15,
                    "network-id": 255,
                    "team-id": "Sauber",
                    "my-team": False,
                    "race-number": 77,
                    "nationality": "Finnish",
                    "name": "BOTTAS",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 2,
                    "network-id": 255,
                    "team-id": "VCARB",
                    "my-team": False,
                    "race-number": 3,
                    "nationality": "Australian",
                    "name": "RICCIARDO",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 7,
                    "network-id": 255,
                    "team-id": "Mercedes",
                    "my-team": False,
                    "race-number": 44,
                    "nationality": "British",
                    "name": "HAMILTON",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 50,
                    "network-id": 255,
                    "team-id": "Mercedes",
                    "my-team": False,
                    "race-number": 63,
                    "nationality": "British",
                    "name": "RUSSELL",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 112,
                    "network-id": 255,
                    "team-id": "McLaren",
                    "my-team": False,
                    "race-number": 81,
                    "nationality": "Australian",
                    "name": "PIASTRI",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 80,
                    "network-id": 255,
                    "team-id": "Sauber",
                    "my-team": False,
                    "race-number": 24,
                    "nationality": "Chinese",
                    "name": "ZHOU",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 14,
                    "network-id": 255,
                    "team-id": "Red Bull Racing",
                    "my-team": False,
                    "race-number": 11,
                    "nationality": "Mexican",
                    "name": "P\u00c9REZ",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 17,
                    "network-id": 255,
                    "team-id": "Alpine",
                    "my-team": False,
                    "race-number": 31,
                    "nationality": "French",
                    "name": "OCON",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 59,
                    "network-id": 255,
                    "team-id": "Alpine",
                    "my-team": False,
                    "race-number": 10,
                    "nationality": "French",
                    "name": "GASLY",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": False,
                    "driver-id": 62,
                    "network-id": 255,
                    "team-id": "Williams",
                    "my-team": False,
                    "race-number": 23,
                    "nationality": "Thai",
                    "name": "ALBON",
                    "telemetry-setting": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "platform": "Steam"
                }
            ]
        }


        parsed_packet = PacketParticipantsData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with an actual game packet
        """

        raw_packet = b'\x14\x01\t\xff\x02\x00!\x16VERSTAPPEN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x0e\xff\x02\x00\x0b4P\xc3\x89REZ\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01:\xff\x01\x00\x105LECLERC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x00\xff\x01\x007MSAINZ\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x07\xff\x00\x00,\nHAMILTON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x11\xff\x05\x00\x1f\x1cOCON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01;\xff\x05\x00\n\x1cGASLY\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x016\xff\x08\x00\x04\nNORRIS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x0f\xff\t\x00M\x1bBOTTAS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01P\xff\t\x00\x18\x0fZHOU\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x03\xff\x04\x00\x0eMALONSO\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x0b\xff\x07\x00\x14\x15MAGNUSSEN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\n\xff\x07\x00\x1b\x1dHULKENBERG\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01^\xff\x06\x00\x16+TSUNODA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01>\xff\x03\x00\x17PALBON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x01\x84\xff\x03\x00\x02\x01SARGEANT\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x012\xff\x00\x00?\nRUSSELL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xff\x00\xff\x01\x08\x00Q\x00das\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\xff\x02\x06\x00\x05\x00kishore_selvaraj\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x03\x00\xff\x00\x04\x00\r%Milk\xc2\xa0Sheik\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\xff\xff\xff\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "num-active-cars": 20,
            "participants": [
                {
                    "ai-controlled": True,
                    "driver-id": 9,
                    "network-id": 255,
                    "team-id": "Red Bull Racing",
                    "my-team": False,
                    "race-number": 33,
                    "nationality": "Dutch",
                    "name": "VERSTAPPEN",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 14,
                    "network-id": 255,
                    "team-id": "Red Bull Racing",
                    "my-team": False,
                    "race-number": 11,
                    "nationality": "Mexican",
                    "name": "P\u00c9REZ",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 58,
                    "network-id": 255,
                    "team-id": "Ferrari",
                    "my-team": False,
                    "race-number": 16,
                    "nationality": "Monegasque",
                    "name": "LECLERC",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 0,
                    "network-id": 255,
                    "team-id": "Ferrari",
                    "my-team": False,
                    "race-number": 55,
                    "nationality": "Spanish",
                    "name": "SAINZ",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 7,
                    "network-id": 255,
                    "team-id": "Mercedes",
                    "my-team": False,
                    "race-number": 44,
                    "nationality": "British",
                    "name": "HAMILTON",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 17,
                    "network-id": 255,
                    "team-id": "Alpine",
                    "my-team": False,
                    "race-number": 31,
                    "nationality": "French",
                    "name": "OCON",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 59,
                    "network-id": 255,
                    "team-id": "Alpine",
                    "my-team": False,
                    "race-number": 10,
                    "nationality": "French",
                    "name": "GASLY",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 54,
                    "network-id": 255,
                    "team-id": "McLaren",
                    "my-team": False,
                    "race-number": 4,
                    "nationality": "British",
                    "name": "NORRIS",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 15,
                    "network-id": 255,
                    "team-id": "Alfa Romeo",
                    "my-team": False,
                    "race-number": 77,
                    "nationality": "Finnish",
                    "name": "BOTTAS",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 80,
                    "network-id": 255,
                    "team-id": "Alfa Romeo",
                    "my-team": False,
                    "race-number": 24,
                    "nationality": "Chinese",
                    "name": "ZHOU",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 3,
                    "network-id": 255,
                    "team-id": "Aston Martin",
                    "my-team": False,
                    "race-number": 14,
                    "nationality": "Spanish",
                    "name": "ALONSO",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 11,
                    "network-id": 255,
                    "team-id": "Haas",
                    "my-team": False,
                    "race-number": 20,
                    "nationality": "Danish",
                    "name": "MAGNUSSEN",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 10,
                    "network-id": 255,
                    "team-id": "Haas",
                    "my-team": False,
                    "race-number": 27,
                    "nationality": "German",
                    "name": "HULKENBERG",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 94,
                    "network-id": 255,
                    "team-id": "Alpha Tauri",
                    "my-team": False,
                    "race-number": 22,
                    "nationality": "Japanese",
                    "name": "TSUNODA",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 62,
                    "network-id": 255,
                    "team-id": "Williams",
                    "my-team": False,
                    "race-number": 23,
                    "nationality": "Thai",
                    "name": "ALBON",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 132,
                    "network-id": 255,
                    "team-id": "Williams",
                    "my-team": False,
                    "race-number": 2,
                    "nationality": "American",
                    "name": "SARGEANT",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": True,
                    "driver-id": 50,
                    "network-id": 255,
                    "team-id": "Mercedes",
                    "my-team": False,
                    "race-number": 63,
                    "nationality": "British",
                    "name": "RUSSELL",
                    "telemetry-setting": "Public",
                    "show-online-names": False,
                    "tech-level": 0,
                    "platform": "Unknown"
                },
                {
                    "ai-controlled": False,
                    "driver-id": 255,
                    "network-id": 1,
                    "team-id": "McLaren",
                    "my-team": False,
                    "race-number": 81,
                    "nationality": "Unspecified",
                    "name": "das",
                    "telemetry-setting": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "platform": "Steam"
                },
                {
                    "ai-controlled": False,
                    "driver-id": 255,
                    "network-id": 2,
                    "team-id": "Alpha Tauri",
                    "my-team": False,
                    "race-number": 5,
                    "nationality": "Unspecified",
                    "name": "kishore_selvaraj",
                    "telemetry-setting": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "platform": "PlayStation"
                },
                {
                    "ai-controlled": False,
                    "driver-id": 255,
                    "network-id": 0,
                    "team-id": "Aston Martin",
                    "my-team": False,
                    "race-number": 13,
                    "nationality": "Indian",
                    "name": "Milk\u00a0Sheik",
                    "telemetry-setting": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "platform": "Steam"
                }
            ]
        }

        parsed_packet = PacketParticipantsData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def _getRandomParticipantData(self, header: PacketHeader, max_length: Optional[int] = 47) -> ParticipantData:
        """
        Generates a random participant data

        Args:
            header (PacketHeader): The header of the packet
            max_length (Optional[int], optional): The maximum length of the username. Defaults to 47.

        Returns:
            ParticipantData: The random participant data
        """

        if header.m_gameYear == 23:
            team_id = random.choice(list(TeamID23))
            tech_level = 0
        elif header.m_gameYear == 24:
            team_id = random.choice(list(TeamID24))
            tech_level = random.getrandbits(16)
        elif header.m_gameYear == 25:
            team_id = random.choice(list(TeamID25))
            tech_level = random.getrandbits(16)
        return ParticipantData.from_values(
            header,
            ai_controlled=F1TypesTest.getRandomBool(),
            driver_id=random.randint(1,100),
            network_id=random.randint(1,100),
            team_id=team_id,
            my_team=F1TypesTest.getRandomBool(),
            race_number=random.randint(1,self.m_num_players),
            nationality=random.choice(list(Nationality)),
            name=F1TypesTest.getRandomUserName(max_length),
            your_telemetry=random.choice(list(TelemetrySetting)),
            show_online_names=F1TypesTest.getRandomBool(),
            platform=random.choice(list(Platform)),
            tech_level=tech_level
        )