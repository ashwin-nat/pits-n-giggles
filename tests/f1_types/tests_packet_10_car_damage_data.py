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
from apps.lib.f1_types import CarDamageData, PacketCarDamageData, F1PacketType, PacketHeader
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

    def test_f1_24_random(self):
        """
        Test for F1 2024 with an randomly generated packet
        """

        generated_test_obj = PacketCarDamageData.from_values(
            self.m_header_24,
            [self._generateRandomCarDamageData() for _ in range(self.m_num_players)]
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
            [self._generateRandomCarDamageData() for _ in range(self.m_num_players)]
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

    def _generateRandomCarDamageData(self) -> CarDamageData:
        """
        Generate a random car damage data object

        Returns:
            LobbyInfoData: A random car damage data object
        """

        return CarDamageData.from_values(
            tyres_wear=[random.uniform(0.0, 100.0) for _ in range(4)],
            tyres_damage=[random.randrange(0, 100) for _ in range(4)],
            brakes_damage=[random.randrange(0, 100) for _ in range(4)],
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
