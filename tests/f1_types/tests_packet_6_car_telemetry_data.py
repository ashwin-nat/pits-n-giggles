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
from lib.f1_types import CarTelemetryData, PacketCarTelemetryData, F1PacketType, PacketHeader
from .tests_parser_base import F1TypesTest

class TestPacketCarTelemetryData(F1TypesTest):
    """
    Tests for TestPacketCarTelemetryData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.CAR_TELEMETRY, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.CAR_TELEMETRY, 24, self.m_num_players)
        self.m_header_25 = F1TypesTest.getRandomHeader(F1PacketType.CAR_TELEMETRY, 25, self.m_num_players)

    def test_f1_24_random(self):
        """
        Test for F1 2024 with an randomly generated packet
        """

        generated_test_obj = PacketCarTelemetryData.from_values(
            self.m_header_24,
            [self._generateRandomCarTelemetryData() for _ in range(self.m_num_players)],
            mfd_panel_index=random.getrandbits(8),
            mfd_panel_index_secondary_player=random.getrandbits(8),
            suggested_gear=random.randrange(1,8)
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketCarTelemetryData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_random(self):
        """
        Test for F1 2023 with an randomly generated packet
        """

        generated_test_obj = PacketCarTelemetryData.from_values(
            self.m_header_23,
            [self._generateRandomCarTelemetryData() for _ in range(self.m_num_players)],
            mfd_panel_index=random.getrandbits(7),
            mfd_panel_index_secondary_player=random.getrandbits(7),
            suggested_gear=random.getrandbits(7)
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_23, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketCarTelemetryData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with an actual packet
        """

        raw_packet = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00````ccccm\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00````ccccm\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00````ccccm\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00````ccccm\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00aaaaddddn\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00________n\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00aaaaddddn\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00________n\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00````````m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00^^^^^^^^m\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00aaaaaaaan\x00ff\xa2Aff\xa2A\x9a\x99\xb5A\x9a\x99\xb5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00'
        expected_json = {
            "car-telemetry-data": [
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        96,
                        96,
                        96,
                        96
                    ],
                    "tyres-inner-temperature": [
                        99,
                        99,
                        99,
                        99
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        96,
                        96,
                        96,
                        96
                    ],
                    "tyres-inner-temperature": [
                        99,
                        99,
                        99,
                        99
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        96,
                        96,
                        96,
                        96
                    ],
                    "tyres-inner-temperature": [
                        99,
                        99,
                        99,
                        99
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        96,
                        96,
                        96,
                        96
                    ],
                    "tyres-inner-temperature": [
                        99,
                        99,
                        99,
                        99
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        97,
                        97,
                        97,
                        97
                    ],
                    "tyres-inner-temperature": [
                        100,
                        100,
                        100,
                        100
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        95,
                        95,
                        95,
                        95
                    ],
                    "tyres-inner-temperature": [
                        95,
                        95,
                        95,
                        95
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        97,
                        97,
                        97,
                        97
                    ],
                    "tyres-inner-temperature": [
                        100,
                        100,
                        100,
                        100
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        95,
                        95,
                        95,
                        95
                    ],
                    "tyres-inner-temperature": [
                        95,
                        95,
                        95,
                        95
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        96,
                        96,
                        96,
                        96
                    ],
                    "tyres-inner-temperature": [
                        96,
                        96,
                        96,
                        96
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "tyres-inner-temperature": [
                        94,
                        94,
                        94,
                        94
                    ],
                    "engine-temperature": 109,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        30,
                        30,
                        30,
                        30
                    ],
                    "tyres-surface-temperature": [
                        97,
                        97,
                        97,
                        97
                    ],
                    "tyres-inner-temperature": [
                        97,
                        97,
                        97,
                        97
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        20.299999237060547,
                        20.299999237060547,
                        22.700000762939453,
                        22.700000762939453
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 0,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 0,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                }
            ],
            "mfd-panel-index": 255,
            "mfd-panel-index-secondary": 255,
            "suggested-gear": 0
        }

        parsed_packet = PacketCarTelemetryData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x18\x00\x18\x00\x18\x00\x18\x00ZZZZZZZZn\x00\xcd\xcc\xa8A\xcd\xcc\xa8A33\xc7A33\xc7A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00e\r\x00\x00\x00\x00\x18\x00\x18\x00\x18\x00\x18\x00ZZZZZZZZn\x00\xcd\xcc\xa8A\xcd\xcc\xa8A33\xc7A33\xc7A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00'
        expected_json = {
            "car-telemetry-data": [
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        24,
                        24,
                        24,
                        24
                    ],
                    "tyres-surface-temperature": [
                        90,
                        90,
                        90,
                        90
                    ],
                    "tyres-inner-temperature": [
                        90,
                        90,
                        90,
                        90
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        21.100000381469727,
                        21.100000381469727,
                        24.899999618530273,
                        24.899999618530273
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 2.802596928649634e-45,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": -0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 3429,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        24,
                        24,
                        24,
                        24
                    ],
                    "tyres-surface-temperature": [
                        90,
                        90,
                        90,
                        90
                    ],
                    "tyres-inner-temperature": [
                        90,
                        90,
                        90,
                        90
                    ],
                    "engine-temperature": 110,
                    "tyres-pressure": [
                        21.100000381469727,
                        21.100000381469727,
                        24.899999618530273,
                        24.899999618530273
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 0,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                },
                {
                    "speed": 0,
                    "throttle": 0.0,
                    "steer": 0.0,
                    "brake": 0.0,
                    "clutch": 0,
                    "gear": 0,
                    "engine-rpm": 0,
                    "drs": False,
                    "rev-lights-percent": 0,
                    "brakes-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-surface-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "tyres-inner-temperature": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "engine-temperature": 0,
                    "tyres-pressure": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "surface-type": [
                        0,
                        0,
                        0,
                        0
                    ]
                }
            ],
            "mfd-panel-index": 255,
            "mfd-panel-index-secondary": 255,
            "suggested-gear": 0
        }

        parsed_packet = PacketCarTelemetryData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def test_f1_25_actual(self):
        """
        Test for F1 2025 with an actual game packet
        """

        raw_packet = b'G\x01\x00\x00\x80?\x1a\xaa\x14\xbc\x00\x00\x00\x00\x00\x08\xcc-\x01O\xff\x7f\xd1\x01\xd1\x01\x0c\x02\x0e\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00D\x01\x00\x00\x80?\xdfTL\xbd\x00\x00\x00\x00\x00\x08g-\x01K\xe0\x7f\xe7\x01\xe7\x01!\x02$\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00P\x01\x00\x00\x80?\x19\xe0\x02\xbc\x00\x00\x00\x00\x00\x08\xcb.\x01Z\xe3\x7f\xa4\x01\xa4\x01\xe1\x01\xe3\x01PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00%\x01\xcd\xcc\xcc>\x18\x0c\xbc:\x00\x00\x00\x00\x00\x08_(\x00\x18\x00\x00\xd9\x01\xd9\x01\x0f\x02\x11\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00P\x01\x00\x00\x80?\x17\xaa\x14\xbb\x00\x00\x00\x00\x00\x08\xa6.\x01Y\xe3\x7f\x9b\x01\x9b\x01\xd7\x01\xd9\x01PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\xcd\x00\x00\x00\x00\x00\xf0\xe6/\xbb\t{\x1c?\x00\x05\x87&\x00\x02\x00\x001\x032\x03*\x03+\x03PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x01\x00\x01\x99\x00\x00\x00\x80?\xfb\x8dV\xbd\x00\x00\x00\x00\x00\x042\'\x00\n\x00\x00R\x03S\x03R\x03V\x03PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x01\x00\x01\x1c\x01\xcd\xcc\xcc>\xaa\xeb\x9b\xbb\x00\x00\x00\x00\x00\x08[\'\x00\x0c\x00\x00\xc2\x01\xc2\x01\xf4\x01\xf6\x01PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\xd1\x00\x00\x00\x00\x00\x8d\xda";Y% ?\x00\x05\xa9)\x00&0\x00N\x03N\x03L\x03M\x03PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x01N\x01\x00\x00\x80?\x13\t\x8d\xbb\x00\x00\x00\x00\x00\x08\xa0.\x01X\xe0?\x83\x01\x83\x01\xbd\x01\xbe\x01PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x002\x01\x00\x00\x80?\xe0\x0c\x08<\x00\x00\x00\x00\x00\x08\x06+\x013\xff\x00\x16\x02\x17\x02M\x02O\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\xd5\x00\x00\x00\x80?UOf\xbb\x00\x00\x00\x00\x00\x06+(\x00\x16\x00\x00\x06\x03\x07\x03\x10\x03\x14\x03PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x01\x00\x01:\x01\x00\x00\x80?\x00\x00\x00\x80\x00\x00\x00\x00\x00\x08\x13,\x01<\xe0\x01\x05\x02\x05\x02>\x02@\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\x0f\x01\x00\x00\x00\x00\x18\x0c\xbc\xba\xfa\x98\x1e?\x00\x07A*\x00,g\x00\xb2\x02\xb2\x02\xbb\x02\xbd\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x001\x01\xcd\xcc\xcc>\x00\x00\x00\x80\x00\x00\x00\x00\x00\x08\x0f*\x00* \x00\x02\x02\x03\x02.\x020\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00N\x01\x00\x00\x80?\xe4\x10\n\xbc\x00\x00\x00\x00\x00\x08\xa2.\x01X\xe1?\xb6\x01\xb7\x01\xf4\x01\xf6\x01PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\xf7\x00\x00\x00\x80?\xf0\xe6/;\x00\x00\x00\x00\x00\x06\x1f,\x00=\xe0\x03\xbb\x02\xbc\x02\xd0\x02\xd3\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00L\x01\x00\x00\x80?\xa3\xd49\xbc\x00\x00\x00\x00\x00\x08y.\x01W\xff\x7f\xc5\x01\xc5\x01\x02\x02\x04\x02PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\x85\x00\xbb\x1fe?\xa6\x1f9\xbe\x00\x00\x00\x00\x00\x03\x1e)\x00!\x00\x00v\x03w\x03v\x03y\x03PPPPPPPPn\x00\x00\x00\xacA\x00\x00\xacAff\xc2Aff\xc2A\x00\x00\x00\x00\x0f\x00\x93\x14\x93>\xd9\xbeg>\x00\x00\x00\x00\x00\x01\xa6\x0f\x00\x00\x00\x00\x9d\x03\x9f\x037\x03g\x03c\x7f@C\\`QS{\x00V\x10\xb2A2\x16\xb4A\x9f1\xc3A\xe4y\xc4A\x04\x04\x04\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00'
        expected_json = {"car-telemetry-data": [{"speed": 327, "throttle": 1.0, "steer": -0.009073758497834206, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11724, "drs": True, "rev-lights-percent": 79, "brakes-temperature": [465, 465, 524, 526], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 324, "throttle": 1.0, "steer": -0.04988562688231468, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11623, "drs": True, "rev-lights-percent": 75, "brakes-temperature": [487, 487, 545, 548], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 336, "throttle": 1.0, "steer": -0.007987999357283115, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11979, "drs": True, "rev-lights-percent": 90, "brakes-temperature": [420, 420, 481, 483], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 293, "throttle": 0.4000000059604645, "steer": 0.0014346865937113762, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 10335, "drs": False, "rev-lights-percent": 24, "brakes-temperature": [473, 473, 527, 529], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 336, "throttle": 1.0, "steer": -0.0022684389259666204, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11942, "drs": True, "rev-lights-percent": 89, "brakes-temperature": [411, 411, 471, 473], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 205, "throttle": 0.0, "steer": -0.0026840530335903168, "brake": 0.6112523674964905, "clutch": 0, "gear": 5, "engine-rpm": 9863, "drs": False, "rev-lights-percent": 2, "brakes-temperature": [817, 818, 810, 811], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 1, 0, 1]}, {"speed": 153, "throttle": 1.0, "steer": -0.052381496876478195, "brake": 0.0, "clutch": 0, "gear": 4, "engine-rpm": 10034, "drs": False, "rev-lights-percent": 10, "brakes-temperature": [850, 851, 850, 854], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 1, 0, 1]}, {"speed": 284, "throttle": 0.4000000059604645, "steer": -0.004758317954838276, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 10075, "drs": False, "rev-lights-percent": 12, "brakes-temperature": [450, 450, 500, 502], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 209, "throttle": 0.0, "steer": 0.0024849504698067904, "brake": 0.6255698800086975, "clutch": 0, "gear": 5, "engine-rpm": 10665, "drs": False, "rev-lights-percent": 38, "brakes-temperature": [846, 846, 844, 845], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 1]}, {"speed": 334, "throttle": 1.0, "steer": -0.004304060246795416, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11936, "drs": True, "rev-lights-percent": 88, "brakes-temperature": [387, 387, 445, 446], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 306, "throttle": 1.0, "steer": 0.008303850889205933, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11014, "drs": True, "rev-lights-percent": 51, "brakes-temperature": [534, 535, 589, 591], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 213, "throttle": 1.0, "steer": -0.0035142500419169664, "brake": 0.0, "clutch": 0, "gear": 6, "engine-rpm": 10283, "drs": False, "rev-lights-percent": 22, "brakes-temperature": [774, 775, 784, 788], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 1, 0, 1]}, {"speed": 314, "throttle": 1.0, "steer": -0.0, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11283, "drs": True, "rev-lights-percent": 60, "brakes-temperature": [517, 517, 574, 576], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 271, "throttle": 0.0, "steer": -0.0014346865937113762, "brake": 0.6195217370986938, "clutch": 0, "gear": 7, "engine-rpm": 10817, "drs": False, "rev-lights-percent": 44, "brakes-temperature": [690, 690, 699, 701], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 305, "throttle": 0.4000000059604645, "steer": -0.0, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 10767, "drs": False, "rev-lights-percent": 42, "brakes-temperature": [514, 515, 558, 560], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 334, "throttle": 1.0, "steer": -0.008426878601312637, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11938, "drs": True, "rev-lights-percent": 88, "brakes-temperature": [438, 439, 500, 502], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 247, "throttle": 1.0, "steer": 0.0026840530335903168, "brake": 0.0, "clutch": 0, "gear": 6, "engine-rpm": 11295, "drs": False, "rev-lights-percent": 61, "brakes-temperature": [699, 700, 720, 723], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 332, "throttle": 1.0, "steer": -0.011342200450599194, "brake": 0.0, "clutch": 0, "gear": 8, "engine-rpm": 11897, "drs": True, "rev-lights-percent": 87, "brakes-temperature": [453, 453, 514, 516], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 133, "throttle": 0.8950154185295105, "steer": -0.18078479170799255, "brake": 0.0, "clutch": 0, "gear": 3, "engine-rpm": 10526, "drs": False, "rev-lights-percent": 33, "brakes-temperature": [886, 887, 886, 889], "tyres-surface-temperature": [80, 80, 80, 80], "tyres-inner-temperature": [80, 80, 80, 80], "engine-temperature": 110, "tyres-pressure": [21.5, 21.5, 24.299999237060547, 24.299999237060547], "surface-type": [0, 0, 0, 0]}, {"speed": 15, "throttle": 0.287266343832016, "steer": 0.22631396353244781, "brake": 0.0, "clutch": 0, "gear": 1, "engine-rpm": 4006, "drs": False, "rev-lights-percent": 0, "brakes-temperature": [925, 927, 823, 871], "tyres-surface-temperature": [99, 127, 64, 67], "tyres-inner-temperature": [92, 96, 81, 83], "engine-temperature": 123, "tyres-pressure": [22.257976531982422, 22.51083755493164, 24.399229049682617, 24.55951690673828], "surface-type": [4, 4, 4, 4]}, {"speed": 0, "throttle": 0.0, "steer": 0.0, "brake": 0.0, "clutch": 0, "gear": 0, "engine-rpm": 0, "drs": False, "rev-lights-percent": 0, "brakes-temperature": [0, 0, 0, 0], "tyres-surface-temperature": [0, 0, 0, 0], "tyres-inner-temperature": [0, 0, 0, 0], "engine-temperature": 0, "tyres-pressure": [0.0, 0.0, 0.0, 0.0], "surface-type": [0, 0, 0, 0]}, {"speed": 0, "throttle": 0.0, "steer": 0.0, "brake": 0.0, "clutch": 0, "gear": 0, "engine-rpm": 0, "drs": False, "rev-lights-percent": 0, "brakes-temperature": [0, 0, 0, 0], "tyres-surface-temperature": [0, 0, 0, 0], "tyres-inner-temperature": [0, 0, 0, 0], "engine-temperature": 0, "tyres-pressure": [0.0, 0.0, 0.0, 0.0], "surface-type": [0, 0, 0, 0]}], "mfd-panel-index": 255, "mfd-panel-index-secondary": 255, "suggested-gear": 0}

        parsed_packet = PacketCarTelemetryData(self.m_header_25, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def _generateRandomCarTelemetryData(self) -> CarTelemetryData:
        """
        Generates random car telemetry data
        """

        return CarTelemetryData.from_values(
            speed=random.randrange(0, 370),
            throttle=F1TypesTest.getRandomFloat(),
            steer=F1TypesTest.getRandomFloat(),
            brake=F1TypesTest.getRandomFloat(),
            clutch=random.randrange(0,100),
            gear=random.randrange(-1,8),
            engine_rpm=random.randrange(0,16000),
            drs=F1TypesTest.getRandomBool(),
            rev_lights_percent=random.randrange(0,100),
            rev_lights_bit_value=random.getrandbits(16),
            brakes_temperature_0=random.getrandbits(16),
            brakes_temperature_1=random.getrandbits(16),
            brakes_temperature_2=random.getrandbits(16),
            brakes_temperature_3=random.getrandbits(16),
            tyres_surface_temperature_0=random.getrandbits(8),
            tyres_surface_temperature_1=random.getrandbits(8),
            tyres_surface_temperature_2=random.getrandbits(8),
            tyres_surface_temperature_3=random.getrandbits(8),
            tyres_inner_temperature_0=random.getrandbits(8),
            tyres_inner_temperature_1=random.getrandbits(8),
            tyres_inner_temperature_2=random.getrandbits(8),
            tyres_inner_temperature_3=random.getrandbits(8),
            engine_temperature=random.getrandbits(16),
            tyres_pressure_0=F1TypesTest.getRandomFloat(),
            tyres_pressure_1=F1TypesTest.getRandomFloat(),
            tyres_pressure_2=F1TypesTest.getRandomFloat(),
            tyres_pressure_3=F1TypesTest.getRandomFloat(),
            surface_type_0=random.getrandbits(8),
            surface_type_1=random.getrandbits(8),
            surface_type_2=random.getrandbits(8),
            surface_type_3=random.getrandbits(8)
        )
