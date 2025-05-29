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
from lib.f1_types import CarDamageData, PacketCarDamageData, F1PacketType, PacketHeader
from .tests_parser_base import F1TypesTest

class TestPacketCarDamageData(F1TypesTest):
    """
    Tests for TestPacketCarDamageData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.CAR_DAMAGE, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.CAR_DAMAGE, 24, self.m_num_players)
        self.m_header_25 = F1TypesTest.getRandomHeader(F1PacketType.CAR_DAMAGE, 25, self.m_num_players)

    def test_f1_25_random(self):
        """
        Test for F1 2025 with an randomly generated packet
        """

        generated_test_obj = PacketCarDamageData.from_values(
            self.m_header_25,
            [self._generateRandomCarDamageData(game_year=25) for _ in range(self.m_num_players)]
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_25, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketCarDamageData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_24_random(self):
        """
        Test for F1 2024 with an randomly generated packet
        """

        generated_test_obj = PacketCarDamageData.from_values(
            self.m_header_24,
            [self._generateRandomCarDamageData(game_year=24) for _ in range(self.m_num_players)]
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_24, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketCarDamageData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_random(self):
        """
        Test for F1 2023 with an randomly generated packet
        """

        generated_test_obj = PacketCarDamageData.from_values(
            self.m_header_23,
            [self._generateRandomCarDamageData(game_year=23) for _ in range(self.m_num_players)]
        )
        serialised_test_obj = generated_test_obj.to_bytes()
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)
        self.assertEqual(self.m_header_23, parsed_header)
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketCarDamageData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with the actual packet
        """

        raw_packet = b'\xbe\xc9\xea8\xae\x95\xd18\xc3\xfd\x898\xfe\xcc\x8d8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x008\xc1\xe57\xf8\xbf\xe27\xd6\xbe\x947\xcbD\x957\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00(\x96d8\xf1@\x0b8\x8d\x8c\x028\x0cw\x847\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00D\xf1\x7f7\xc2\x8d\x827\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1eB\x0f9\xa4\xc2\xe58\x1c6\x8e8\xdd$\x9a8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc9\x10\x957e\xf1\x907\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\xae\x887\xf3\xb2\x8b7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00x\x06\x078\xb6\x14\xa67\x1c\x0fQ7\xa4\xceP7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "car-damage-data": [
                {
                    "tyres-wear": [
                        0.00011195566912647337,
                        9.99377662083134e-05,
                        6.579935870831832e-05,
                        6.761586701031774e-05
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        2.73889017989859e-05,
                        2.703069185372442e-05,
                        1.7731839761836454e-05,
                        1.7794218365452252e-05
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        5.4499279940500855e-05,
                        3.320066389278509e-05,
                        3.112531339866109e-05,
                        1.579106174176559e-05
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        1.5255358448484913e-05,
                        1.556321876705624e-05,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0001366217329632491,
                        0.00010955825564451516,
                        6.781166302971542e-05,
                        7.35015855752863e-05
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        1.7770000340533443e-05,
                        1.7278545783483423e-05,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        1.6293950466206297e-05,
                        1.6653420971124433e-05,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        3.219253267161548e-05,
                        1.9798386347247288e-05,
                        1.2460888683563098e-05,
                        1.2445878383005038e-05
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                }
            ]
        }

        parsed_packet = PacketCarDamageData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {
            "car-damage-data": [
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                },
                {
                    "tyres-wear": [
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ],
                    "tyres-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "brakes-damage": [
                        0,
                        0,
                        0,
                        0
                    ],
                    "front-left-wing-damage": 0,
                    "front-right-wing-damage": 0,
                    "rear-wing-damage": 0,
                    "floor-damage": 0,
                    "diffuser-damage": 0,
                    "sidepod-damage": 0,
                    "drs-fault": False,
                    "ers-fault": False,
                    "gear-box-damage": 0,
                    "engine-damage": 0,
                    "engine-mguh-wear": 0,
                    "engine-es-wear": 0,
                    "engine-ce-wear": 0,
                    "engine-ice-wear": 0,
                    "engine-mguk-wear": 0,
                    "engine-tc-wear": 0,
                    "engine-blown": False,
                    "engine-seized": False
                }
            ]
        }

        parsed_packet = PacketCarDamageData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def test_f1_25_actual(self):

        raw_payload = b"\xc3Cc?\x0b\xefx?\xa3\x7f:?\xe9\xe1&?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1d\xd4k?VT\x87?'\xb9\xf7>M\xcb\x14?\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8bT\x98?4O\x98?\xec8\x82?)q1?\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe6\x0f\x9a?\xcb.\x9a?\x9di{?x\x19S?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\x13\x8b?k\x8d\x98?A\x1eh?\x08h!?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00M\x85\x8b?=\x88\x94?\x80\xc2R?{yS?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00l\xd9\x81?\xe5L\x8f?\xa3\xb1C?\x80\xa6r?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08Q\x9a?\xcd\x03\xac?\xb4d[?\x19\xee\x91?\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x172\x7f?n\xca\x8d?,k'?\xc67\x82?\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf4\xe2s?\x8eS\x93?5s6?\x88rg?\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00~\xb2[?\r\x90q?\x92\xb1\xe1>90\x01?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1a\x05\x92?\xeex\x98?\x94b`?m\xc6q?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xbf\xfay?t\x07\x8d?\xc8\x89$?\n\x90\x1f?\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\xfa\x82?\xc8\x92\x90?\x86#4?\x05\x10A?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb6S\x97?\xfb\x90\xb1?%\xecQ?d\x1b\xab?\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00`\xb8\x80?B\xc4\x86?\x12\xd14?\xcd>\x15?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb8R\x81?<\xf9\x8f?\xc523?\x19nW?\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00. R?\xbe\xc0h?\x89\xaa\x19?\x06\xe2\x16?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\xc5l?~\x9f\x89?b\x9eQ?I\xe1\x86?\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00K\xa7\xc2?\xaa\\\xe5?5\x14\xaa?Q\x18}?\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        expected_json = {"car-damage-data": [{"tyres-wear": [0.8877527117729187, 0.97239750623703, 0.7285100817680359, 0.6518846154212952], "tyres-damage": [0, 0, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.9212053418159485, 1.0572612285614014, 0.48383447527885437, 0.5812271237373352], "tyres-damage": [0, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.1900800466537476, 1.1899170875549316, 1.017362117767334, 0.6931329369544983], "tyres-damage": [1, 1, 1, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.2036101818084717, 1.2045530080795288, 0.9820802807807922, 0.8246073722839355], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.086530327796936, 1.191815733909607, 0.9067116379737854, 0.6304936408996582], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.0900055170059204, 1.1604076623916626, 0.8232803344726562, 0.8260723948478699], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.0144476890563965, 1.1195341348648071, 0.7644292712211609, 0.9478530883789062], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.2055978775024414, 1.343865990638733, 0.8570053577423096, 1.1400786638259888], "tyres-damage": [1, 1, 0, 1], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.9968580603599548, 1.1077401638031006, 0.6539790630340576, 1.017327070236206], "tyres-damage": [0, 1, 0, 1], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.9526817798614502, 1.1509873867034912, 0.7126954197883606, 0.9040913581848145], "tyres-damage": [0, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.8581923246383667, 0.9436042904853821, 0.44080787897109985, 0.5046420693397522], "tyres-damage": [0, 0, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.1407806873321533, 1.191190481185913, 0.8765041828155518, 0.9444339871406555], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.9764823317527771, 1.101789951324463, 0.6427273750305176, 0.6232916116714478], "tyres-damage": [0, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.0232564210891724, 1.1294794082641602, 0.7036670446395874, 0.7541506886482239], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.1822421550750732, 1.3872369527816772, 0.8200095295906067, 1.33677339553833], "tyres-damage": [1, 1, 0, 1], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.0056266784667969, 1.0528643131256104, 0.7063151597976685, 0.582989513874054], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.0103368759155273, 1.124793529510498, 0.6999934315681458, 0.8415237069129944], "tyres-damage": [1, 1, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.8208035230636597, 0.9091910123825073, 0.6002584099769592, 0.5893863439559937], "tyres-damage": [0, 0, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.9248819351196289, 1.0751798152923584, 0.818822979927063, 1.0537501573562622], "tyres-damage": [0, 1, 0, 1], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [1.5207303762435913, 1.7918903827667236, 1.3287416696548462, 0.9886522889137268], "tyres-damage": [1, 1, 1, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.0, 0.0, 0.0, 0.0], "tyres-damage": [0, 0, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}, {"tyres-wear": [0.0, 0.0, 0.0, 0.0], "tyres-damage": [0, 0, 0, 0], "brakes-damage": [0, 0, 0, 0], "front-left-wing-damage": 0, "front-right-wing-damage": 0, "rear-wing-damage": 0, "floor-damage": 0, "diffuser-damage": 0, "sidepod-damage": 0, "drs-fault": False, "ers-fault": False, "gear-box-damage": 0, "engine-damage": 0, "engine-mguh-wear": 0, "engine-es-wear": 0, "engine-ce-wear": 0, "engine-ice-wear": 0, "engine-mguk-wear": 0, "engine-tc-wear": 0, "engine-blown": False, "engine-seized": False}]}

        parsed_packet = PacketCarDamageData(self.m_header_25, raw_payload)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)

    def _generateRandomCarDamageData(self, game_year: int) -> CarDamageData:
        """
        Generate a random car damage data object

        Args:
            game_year (int): The game year

        Returns:
            LobbyInfoData: A random car damage data object
        """

        return CarDamageData.from_values(
            game_year=game_year,
            tyres_wear=[random.uniform(0.0, 100.0) for _ in range(4)],
            tyres_damage=[random.randrange(0, 100) for _ in range(4)],
            brakes_damage=[random.randrange(0, 100) for _ in range(4)],
            tyre_blisters=[random.randrange(0, 100) for _ in range(4)],
            fl_wing_damage=random.randrange(0, 100),
            fr_wing_damage=random.randrange(0, 100),
            rear_wing_damage=random.randrange(0, 100),
            floor_damage=random.randrange(0, 100),
            diffuser_damage=random.randrange(0, 100),
            sidepod_damage=random.randrange(0, 100),
            drs_fault=F1TypesTest.getRandomBool(),
            ers_fault=F1TypesTest.getRandomBool(),
            gear_box_damage=random.randrange(0, 100),
            engine_damage=random.randrange(0, 100),
            engine_mguh_wear=random.randrange(0, 100),
            engine_es_wear=random.randrange(0, 100),
            engine_ce_wear=random.randrange(0, 100),
            engine_ice_wear=random.randrange(0, 100),
            engine_mguk_wear=random.randrange(0, 100),
            engine_tc_wear=random.randrange(0, 100),
            engine_blown=F1TypesTest.getRandomBool(),
            engine_seized=F1TypesTest.getRandomBool()
        )
