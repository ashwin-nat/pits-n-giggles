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

from lib.f1_types import (F1PacketType, LobbyInfoData, Nationality,
                          PacketHeader, PacketLobbyInfoData, Platform,
                          TeamID23, TeamID24, TeamID25, TelemetrySetting)

from .tests_parser_base import F1TypesTest


class TestPacketLobbyInfoData(F1TypesTest):
    """
    Tests for TestPacketLobbyInfoData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.LOBBY_INFO, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.LOBBY_INFO, 24, self.m_num_players)
        self.m_header_25 = F1TypesTest.getRandomHeader(F1PacketType.LOBBY_INFO, 25, self.m_num_players)

    def test_f1_25_random(self):
        """
        Test for F1 2025 with an randomly generated packet
        """

        random_participants = [self._generateRandomLobbyInfoData(self.m_header_25) for _ in range(self.m_num_players)]
        generated_test_obj = PacketLobbyInfoData.from_values(
            self.m_header_25,
            self.m_num_players,
            random_participants
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_25, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketLobbyInfoData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_24_random(self):
        """
        Test for F1 2024 with an randomly generated packet
        """

        random_participants = [self._generateRandomLobbyInfoData(self.m_header_24) for _ in range(self.m_num_players)]
        generated_test_obj = PacketLobbyInfoData.from_values(
            self.m_header_24,
            self.m_num_players,
            random_participants
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketLobbyInfoData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_random(self):
        """
        Test for F1 2023 with an randomly generated packet
        """

        generated_test_obj = PacketLobbyInfoData.from_values(
            self.m_header_23,
            self.m_num_players,
            [self._generateRandomLobbyInfoData(self.m_header_23) for _ in range(self.m_num_players)]
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_23, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketLobbyInfoData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with the actual data
        """

        raw_packet = b'\x14\x00\x04%\x01Milk\xc2\xa0Sheik\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\r\x00\x01\x02\x16\xffMax VERSTAPPEN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\x01\x01\x024\xffSergio P\xc3\x89REZ\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0b\x01\x01\x015\xffCharles LECLERC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x01\x01\x01M\xffCarlos SAINZ\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x007\x01\x01\x00\n\xffLewis HAMILTON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00,\x01\x01\x05\x1c\xffEsteban OCON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1f\x01\x01\x05\x1c\xffPierre GASLY\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x01\x08\n\xffLando NORRIS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x01\t\x1b\xffValtteri BOTTAS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00M\x00\x01\t\x0f\xffZHOU Guanyu\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18\x00\x01\x04M\xffFernando ALONSO\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0e\x00\x01\x07\x15\xffKevin MAGNUSSEN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\x00\x01\x07\x1d\xffNico HULKENBERG\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1b\x00\x01\x06+\xffYuki TSUNODA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x16\x00\x01\x03P\xffAlexander ALBON\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x17\x00\x01\x03\x01\xffLogan SARGEANT\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x08\x00\x01OmG\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Q\x00\x01\x00\n\xffGeorge RUSSELL\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x00\x00\x06\x00\x03UserNameIsFake69\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x01\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "num-players": 20,
            "lobby-players": [
                {
                    "ai-controlled": False,
                    "team-id": "Aston Martin",
                    "nationality": "Indian",
                    "platform": "Steam",
                    "name": "Milk\u00a0Sheik",
                    "car-number": 13,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Red Bull Racing",
                    "nationality": "Dutch",
                    "platform": "Unknown",
                    "name": "Max VERSTAPPEN",
                    "car-number": 33,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Red Bull Racing",
                    "nationality": "Mexican",
                    "platform": "Unknown",
                    "name": "Sergio P\u00c9REZ",
                    "car-number": 11,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Ferrari",
                    "nationality": "Monegasque",
                    "platform": "Unknown",
                    "name": "Charles LECLERC",
                    "car-number": 16,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Ferrari",
                    "nationality": "Spanish",
                    "platform": "Unknown",
                    "name": "Carlos SAINZ",
                    "car-number": 55,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Mercedes",
                    "nationality": "British",
                    "platform": "Unknown",
                    "name": "Lewis HAMILTON",
                    "car-number": 44,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Alpine",
                    "nationality": "French",
                    "platform": "Unknown",
                    "name": "Esteban OCON",
                    "car-number": 31,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Alpine",
                    "nationality": "French",
                    "platform": "Unknown",
                    "name": "Pierre GASLY",
                    "car-number": 10,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "McLaren",
                    "nationality": "British",
                    "platform": "Unknown",
                    "name": "Lando NORRIS",
                    "car-number": 4,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Alfa Romeo",
                    "nationality": "Finnish",
                    "platform": "Unknown",
                    "name": "Valtteri BOTTAS",
                    "car-number": 77,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Alfa Romeo",
                    "nationality": "Chinese",
                    "platform": "Unknown",
                    "name": "ZHOU Guanyu",
                    "car-number": 24,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Aston Martin",
                    "nationality": "Spanish",
                    "platform": "Unknown",
                    "name": "Fernando ALONSO",
                    "car-number": 14,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Haas",
                    "nationality": "Danish",
                    "platform": "Unknown",
                    "name": "Kevin MAGNUSSEN",
                    "car-number": 20,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Haas",
                    "nationality": "German",
                    "platform": "Unknown",
                    "name": "Nico HULKENBERG",
                    "car-number": 27,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Alpha Tauri",
                    "nationality": "Japanese",
                    "platform": "Unknown",
                    "name": "Yuki TSUNODA",
                    "car-number": 22,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Williams",
                    "nationality": "Thai",
                    "platform": "Unknown",
                    "name": "Alexander ALBON",
                    "car-number": 23,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Williams",
                    "nationality": "American",
                    "platform": "Unknown",
                    "name": "Logan SARGEANT",
                    "car-number": 2,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "McLaren",
                    "nationality": "Unspecified",
                    "platform": "Steam",
                    "name": "OmG",
                    "car-number": 81,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": True,
                    "team-id": "Mercedes",
                    "nationality": "British",
                    "platform": "Unknown",
                    "name": "George RUSSELL",
                    "car-number": 63,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Alpha Tauri",
                    "nationality": "Unspecified",
                    "platform": "PlayStation",
                    "name": "UserNameIsFake69",
                    "car-number": 5,
                    "your-telemetry": "Public",
                    "show-online-names": True,
                    "tech-level": 0,
                    "ready-status": "READY"
                }
            ]
        }

        parsed_packet = PacketLobbyInfoData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)


    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'\t\x00\xff\x00\x01Milk\xc2\xa0Sheik\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x01\x01g\x00\x00\x00\x04\x1c\x01Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00d\x00\x01\x00\x01\x07\x03Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00.\x00\x00d\x00\x01\x00\x02\x07\x03Andre-1502Horst\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\x00\x01l\x00\x01\x00\x00\x1d\x03Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\x00\x00u\x00\x01\x00\x05%\x06Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00-\x00\x00d\x00\x00\x00\x08\x1d\x03Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00c\x00\x00d\x00\x00\x00\x08\x00\x04Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00d\x00\x01\x00\x02\x00\x03Player\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00d\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "num-players": 9,
            "lobby-players": [
                {
                    "ai-controlled": False,
                    "team-id": "MY_TEAM",
                    "nationality": "Unspecified",
                    "platform": "Steam",
                    "name": "Milk\u00a0Sheik",
                    "car-number": 5,
                    "your-telemetry": "Public",
                    "show-online-names": 1,
                    "tech-level": 103,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Aston Martin",
                    "nationality": "French",
                    "platform": "Steam",
                    "name": "Player",
                    "car-number": 7,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 100,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Ferrari",
                    "nationality": "Belgian",
                    "platform": "PlayStation",
                    "name": "Player",
                    "car-number": 46,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 100,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Red Bull Racing",
                    "nationality": "Belgian",
                    "platform": "PlayStation",
                    "name": "Andre-1502Horst",
                    "car-number": 19,
                    "your-telemetry": "Restricted",
                    "show-online-names": 1,
                    "tech-level": 108,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Mercedes",
                    "nationality": "German",
                    "platform": "PlayStation",
                    "name": "Player",
                    "car-number": 19,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 117,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Alpine",
                    "nationality": "Indian",
                    "platform": "Origin",
                    "name": "Player",
                    "car-number": 45,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 100,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "McLaren",
                    "nationality": "German",
                    "platform": "PlayStation",
                    "name": "Player",
                    "car-number": 99,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 100,
                    "ready-status": "NOT_READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "McLaren",
                    "nationality": "Unspecified",
                    "platform": "Xbox",
                    "name": "Player",
                    "car-number": 5,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 100,
                    "ready-status": "READY"
                },
                {
                    "ai-controlled": False,
                    "team-id": "Red Bull Racing",
                    "nationality": "Unspecified",
                    "platform": "PlayStation",
                    "name": "Player",
                    "car-number": 5,
                    "your-telemetry": "Restricted",
                    "show-online-names": 0,
                    "tech-level": 100,
                    "ready-status": "NOT_READY"
                }
            ]
        }

        parsed_packet = PacketLobbyInfoData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def _generateRandomLobbyInfoData(self, header: PacketHeader) -> LobbyInfoData:
        """
        Generate a random lobby info data object

        Args:
            header (PacketHeader): The header of the packet

        Returns:
            LobbyInfoData: A random lobby info data object
        """

        if header.m_gameYear == 23:
            return LobbyInfoData.from_values(
                header=header,
                ai_controlled=F1TypesTest.getRandomBool(),
                team_id=random.choice(list(TeamID23)),
                nationality=random.choice(list(Nationality)),
                platform=random.choice(list(Platform)),
                name=F1TypesTest.getRandomUserName(),
                car_number=random.randint(1, 99),
            )
        if header.m_gameYear == 24:
            return LobbyInfoData.from_values(
                header=header,
                ai_controlled=F1TypesTest.getRandomBool(),
                team_id=random.choice(list(TeamID24)),
                nationality=random.choice(list(Nationality)),
                platform=random.choice(list(Platform)),
                name=F1TypesTest.getRandomUserName(),
                car_number=random.randint(1, 99),
                your_telemetry=random.choice(list(TelemetrySetting)),
                show_online_names=F1TypesTest.getRandomBool(),
                tech_level=random.randrange(0,5000),
                ready_status=random.choice(list(LobbyInfoData.ReadyStatus))
            )
        if header.m_gameYear == 25:
            return LobbyInfoData.from_values(
                header=header,
                ai_controlled=F1TypesTest.getRandomBool(),
                team_id=random.choice(list(TeamID25)),
                nationality=random.choice(list(Nationality)),
                platform=random.choice(list(Platform)),
                name=F1TypesTest.getRandomUserName(),
                car_number=random.randint(1, 99),
                your_telemetry=random.choice(list(TelemetrySetting)),
                show_online_names=F1TypesTest.getRandomBool(),
                tech_level=random.randrange(0,5000),
                ready_status=random.choice(list(LobbyInfoData.ReadyStatus))
            )

        # TODO: Implement for 25

        raise NotImplementedError(f"Test not implemented for game year {header.m_gameYear}")