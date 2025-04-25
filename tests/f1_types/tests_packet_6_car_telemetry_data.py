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
