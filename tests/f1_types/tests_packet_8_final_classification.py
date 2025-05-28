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
from lib.f1_types import FinalClassificationData, PacketFinalClassificationData, F1PacketType, \
    PacketHeader, ResultStatus, VisualTyreCompound, ActualTyreCompound
from .tests_parser_base import F1TypesTest

class TestPacketFinalClassificationData(F1TypesTest):
    """
    Tests for TestPacketFinalClassificationData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.FINAL_CLASSIFICATION, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.FINAL_CLASSIFICATION, 24, self.m_num_players)

    def test_f1_24_random(self):
        """
        Test for F1 2024 with an randomly generated packet
        """

        generated_test_obj = PacketFinalClassificationData.from_values(
            self.m_header_24,
            self.m_num_players,
            [self._generateRandomFinalClassificationData(game_year=24) for _ in range(self.m_num_players)]
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketFinalClassificationData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_random(self):
        """
        Test for F1 2023 with an randomly generated packet
        """

        generated_test_obj = PacketFinalClassificationData.from_values(
            self.m_header_23,
            self.m_num_players,
            [self._generateRandomFinalClassificationData(game_year=23) for _ in range(self.m_num_players)]
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_23, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketFinalClassificationData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with an actual packet
        """

        raw_packet = b'\x14\n\x05\x0b\x01\x00\x03\xe5l\x01\x00\x00\x00\x00\xc0 S~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x0c\x05\x0f\x00\x00\x03Bl\x01\x00\x00\x00\x00\xe0(\x87~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\t\x05\t\x02\x00\x03il\x01\x00\x00\x00\x00 \x937~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x02\x05\x04\x12\x00\x03\xc5i\x01\x00\x00\x00\x00\xa0\x8f\x9d}@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x11\x05\x10\x00\x00\x03*o\x01\x00\x00\x00\x00\xe0\x17\xed~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x03\x05\x03\x0f\x00\x03\xabi\x01\x00\x00\x00\x00\xe0>\xa1}@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x04\x05\x05\x0c\x00\x03\xf9i\x01\x00\x00\x00\x00\xc0\x9c\xbf}@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x13\x05\x13\x00\x00\x03 n\x01\x00\x00\x00\x00\x00\xf4\t\x7f@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x07\x05\x08\x06\x00\x03\xf2j\x01\x00\x00\x00\x00\xc0\x16\x01~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x10\x05\x12\x00\x00\x03^m\x01\x00\x00\x00\x00@\xbb\xe4~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x01\x05\x01\x1a\x00\x03^i\x01\x00\x00\x00\x00\xc0\xd1}}@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x0f\x05\x11\x00\x00\x03\xa0m\x01\x00\x00\x00\x00\x807\xd6~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x06\x05\x07\x08\x00\x03\xf9i\x01\x00\x00\x00\x00\xc0\xbb\xd9}@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x05\x05\x06\n\x00\x03Mj\x01\x00\x00\x00\x00@\xb7\xcc}@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x12\x05\x14\x00\x00\x03\xc3m\x01\x00\x00\x00\x00 \x18\xee~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x08\x05\n\x04\x00\x03\xcej\x01\x00\x00\x00\x00@>)~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x0b\x05\r\x00\x00\x03\xe5l\x01\x00\x00\x00\x00\xa0\x07\x82~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x0e\x05\x0e\x00\x00\x03\x0cn\x01\x00\x00\x00\x00@\x9a\xc3~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\r\x05\x0c\x00\x00\x03\xe3m\x01\x00\x00\x00\x00\xc0[\x8e~@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x14\x00\x02\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x80\xe2\xae7@\x00\x00\x01\x12\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "num-cars": 20,
            "classification-data": [
                {
                    "position": 10,
                    "num-laps": 5,
                    "grid-position": 11,
                    "points": 1,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93413,
                    "best-lap-time-str": "01:33.413",
                    "total-race-time": 485.19549560546875,
                    "total-race-time-str": "08:05.195",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 12,
                    "num-laps": 5,
                    "grid-position": 15,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93250,
                    "best-lap-time-str": "01:33.250",
                    "total-race-time": 488.4474792480469,
                    "total-race-time-str": "08:08.447",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 9,
                    "num-laps": 5,
                    "grid-position": 9,
                    "points": 2,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93289,
                    "best-lap-time-str": "01:33.289",
                    "total-race-time": 483.4734191894531,
                    "total-race-time-str": "08:03.473",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 2,
                    "num-laps": 5,
                    "grid-position": 4,
                    "points": 18,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92613,
                    "best-lap-time-str": "01:32.613",
                    "total-race-time": 473.8475646972656,
                    "total-race-time-str": "07:53.847",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 17,
                    "num-laps": 5,
                    "grid-position": 16,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93994,
                    "best-lap-time-str": "01:33.994",
                    "total-race-time": 494.8183288574219,
                    "total-race-time-str": "08:14.818",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 3,
                    "num-laps": 5,
                    "grid-position": 3,
                    "points": 15,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92587,
                    "best-lap-time-str": "01:32.587",
                    "total-race-time": 474.0778503417969,
                    "total-race-time-str": "07:54.077",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 4,
                    "num-laps": 5,
                    "grid-position": 5,
                    "points": 12,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92665,
                    "best-lap-time-str": "01:32.665",
                    "total-race-time": 475.97576904296875,
                    "total-race-time-str": "07:55.975",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 19,
                    "num-laps": 5,
                    "grid-position": 19,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93728,
                    "best-lap-time-str": "01:33.728",
                    "total-race-time": 496.6220703125,
                    "total-race-time-str": "08:16.622",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 7,
                    "num-laps": 5,
                    "grid-position": 8,
                    "points": 6,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92914,
                    "best-lap-time-str": "01:32.914",
                    "total-race-time": 480.06805419921875,
                    "total-race-time-str": "08:00.068",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 16,
                    "num-laps": 5,
                    "grid-position": 18,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93534,
                    "best-lap-time-str": "01:33.534",
                    "total-race-time": 494.29571533203125,
                    "total-race-time-str": "08:14.295",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 1,
                    "num-laps": 5,
                    "grid-position": 1,
                    "points": 26,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92510,
                    "best-lap-time-str": "01:32.510",
                    "total-race-time": 471.86370849609375,
                    "total-race-time-str": "07:51.863",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 15,
                    "num-laps": 5,
                    "grid-position": 17,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93600,
                    "best-lap-time-str": "01:33.600",
                    "total-race-time": 493.3885498046875,
                    "total-race-time-str": "08:13.388",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 6,
                    "num-laps": 5,
                    "grid-position": 7,
                    "points": 8,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92665,
                    "best-lap-time-str": "01:32.665",
                    "total-race-time": 477.60833740234375,
                    "total-race-time-str": "07:57.608",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 5,
                    "num-laps": 5,
                    "grid-position": 6,
                    "points": 10,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92749,
                    "best-lap-time-str": "01:32.749",
                    "total-race-time": 476.79473876953125,
                    "total-race-time-str": "07:56.794",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 18,
                    "num-laps": 5,
                    "grid-position": 20,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93635,
                    "best-lap-time-str": "01:33.635",
                    "total-race-time": 494.8808898925781,
                    "total-race-time-str": "08:14.880",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 8,
                    "num-laps": 5,
                    "grid-position": 10,
                    "points": 4,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 92878,
                    "best-lap-time-str": "01:32.878",
                    "total-race-time": 482.57769775390625,
                    "total-race-time-str": "08:02.577",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 11,
                    "num-laps": 5,
                    "grid-position": 13,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93413,
                    "best-lap-time-str": "01:33.413",
                    "total-race-time": 488.1268615722656,
                    "total-race-time-str": "08:08.126",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 14,
                    "num-laps": 5,
                    "grid-position": 14,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93708,
                    "best-lap-time-str": "01:33.708",
                    "total-race-time": 492.22515869140625,
                    "total-race-time-str": "08:12.225",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 13,
                    "num-laps": 5,
                    "grid-position": 12,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "FINISHED",
                    "best-lap-time-ms": 93667,
                    "best-lap-time-str": "01:33.667",
                    "total-race-time": 488.89739990234375,
                    "total-race-time-str": "08:08.897",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                },
                {
                    "position": 20,
                    "num-laps": 0,
                    "grid-position": 2,
                    "points": 0,
                    "num-pit-stops": 0,
                    "result-status": "DID_NOT_FINISH",
                    "best-lap-time-ms": 0,
                    "best-lap-time-str": "00:00.000",
                    "total-race-time": 23.683143615722656,
                    "total-race-time-str": "00:23.683",
                    "penalties-time": 0,
                    "num-penalties": 0,
                    "num-tyre-stints": 1,
                    "tyre-stints-actual": [
                        "C3"
                    ],
                    "tyre-stints-visual": [
                        "Soft"
                    ],
                    "tyre-stints-end-laps": [
                        255
                    ]
                }
            ]
        }

        parsed_packet = PacketFinalClassificationData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def _generateRandomFinalClassificationData(self, game_year: int) -> FinalClassificationData:
        """
        Generate a random car status data object

        Args:
            game_year (int): Game year

        Returns:
            FinalClassificationData: A random car status data object
        """

        return FinalClassificationData.from_values(
            game_year=game_year,
            position=random.randrange(1,22),
            num_laps=random.randrange(0,70),
            grid_position=random.randrange(1,22),
            points=random.randrange(0,30),
            num_pit_stops=random.randrange(0,4),
            result_status=random.choice(list(ResultStatus)),
            best_lap_time_in_ms=random.getrandbits(24),
            total_race_time=F1TypesTest.getRandomFloat(),
            penalties_time=random.randrange(0,80),
            num_penalties=random.randrange(0,20),
            num_tyre_stints=random.randrange(0,8),
            # tyre_stints_actual,  # array of 8
            tyre_stints_actual_0=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_1=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_2=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_3=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_4=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_5=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_6=random.choice(list(ActualTyreCompound)),
            tyre_stints_actual_7=random.choice(list(ActualTyreCompound)),
            # tyre_stints_visual,  # array of 8
            tyre_stints_visual_0=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_1=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_2=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_3=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_4=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_5=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_6=random.choice(list(VisualTyreCompound)),
            tyre_stints_visual_7=random.choice(list(VisualTyreCompound)),
            # tyre_stints_end_laps,  # array of 8
            tyre_stints_end_laps_0=random.randrange(0,22),
            tyre_stints_end_laps_1=random.randrange(0,22),
            tyre_stints_end_laps_2=random.randrange(0,22),
            tyre_stints_end_laps_3=random.randrange(0,22),
            tyre_stints_end_laps_4=random.randrange(0,22),
            tyre_stints_end_laps_5=random.randrange(0,22),
            tyre_stints_end_laps_6=random.randrange(0,22),
            tyre_stints_end_laps_7=random.randrange(0,22)
        )
