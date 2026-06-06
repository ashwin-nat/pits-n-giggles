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
from lib.f1_types import PacketMotionData, CarMotionData, PacketHeader, F1PacketType
from .tests_parser_base import F1TypesTest

class TestPacketCarMotionData(F1TypesTest):
    """
    Tests for PacketMotionData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = random.randint(1, 22)
        self.m_num_players_26 = random.randint(1, 24)
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.MOTION, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.MOTION, 24, self.m_num_players)
        self.m_header_25 = F1TypesTest.getRandomHeader(F1PacketType.MOTION, 25, self.m_num_players)
        self.m_header_26 = F1TypesTest.getRandomHeader(F1PacketType.MOTION, 26, self.m_num_players_26)
        self.m_packet_23_24_25 = (
            b'\x0c\xb3\x87\xc3\xc8\x98kA\x88\xe74\xc4A\xf7=9\x0e\x89\x82\xba\n\x1f5\xba\xfe\xba\x02\x015\x94\xcck\xc8'
            b'\x00\xff\xbab\x11\xfc6\xa7R!7\x98Zk\xb7\n\x9e$\xc0\x80$\x01\xbc\'D\xc8\xbb\x82k\x93\xc3\xd0\x03}AI\xcaA'
            b'\xc4\xb2\x83\x08;\xa1\xb6\xfd\xb9\xe2gi;\xa1\xbb\xd2\x00\xcd\x933l\x88\xff\xa0\xbb\xafA_5\xa2\x9c+6\x84'
            b'\x98\x8a6\xbb\xfe$\xc0\x00K\xd2\xbb\xcb\x01q;t\xd2\x8a\xc3\xe9usAV\x04;\xc4lPd\xb9\xd8$\x9f\xba\xf2X\xaf'
            b'\xb9\x9e\xbb\xd4\x00\xcf\x932l=\x00\x9e\xbb\xa8\xdc\xf55\xfc\xf7\xba\xb7\x08\xb9\xdf\xb7\r\xfd$\xc0\x00'
            b'\x00\xd5\xbb?w\xf5\xbaN\x9d\x86\xc3\x9d\xb8nA\xfd\x9e7\xc4&\xdaf:\xe7\x11\x8e\xba\x97b\x1a;\x9c\xbb\xcc'
            b'\x00\xd0\x930l\x95\x00\x9c\xbb\xd0\n\x81\xb7e\xc4\xf1\xb7\x87\xa0\xff7\x97\xfb$\xc0\x00t\xcc\xbb\xb3\xbc'
            b'\x95\xbbF{\x82\xc3\xbf\xefiA\xab04\xc4"*\xc3:~\xe4;\xba\x91X\x80\xba?\xbc\xd6\x00j\x93\x97l\x00\x01@\xbc|'
            b'\x92\x9b\xb6\x00\xc0\x026\xa3\x08\xb46\xd1[%\xc0\x00\xd6\xd6\xbb\xc89\x00\xbc\xd41\x90\xc3\x1b\xccuAG'
            b'\xb6;\xc4\xab\x02\x91:\x83\xbc\x86\xba\xe2\xd2\x1c;\x9c\xbb\xf4\x00\xd0\x930l,\x00\x9c\xbb6\xb2\x0f7\xb4'
            b'\xd9\xa77.3W\xb7\xa5\xfb$\xc0\x00<\xf4\xbb\x98\x07\xb0\xba\x86x\x94\xc3\xb7\xd4zA\x1e\x17?\xc4\xf6+x:\nF'
            b'\x98\xba\xcf\xa0\';\xfe\xba\xeb\x005\x94\xcbk\x03\x00\xfd\xbaYA\xff\xb6\x02\r\x89\xb7\xe2\xa9\x116\xb1'
            b'\x9d$\xc0\x00\x0e\xeb\xbb\x04\x92\xef\xb8\xc4#\x8f\xc3\xbf9xA3f>\xc4R\xc4k\xb9\x95\x02\xca\xba\xac\xf9'
            b'\x91\xb9a\xba\xdb\x00\x9a\x94fk\xe9\xff`\xbaw\x98\x0b6\xb6\x9a\xfa4\xff-\xa35\x86@$\xc0\x00Y\xdb\xbb\xd1'
            b'\xdb?:\x17J\x83\xc3$\x97fAQ\x901\xc4,U\x9f\xb9H\xd1{:\xac\xbdq\xba\x13\xbd\xfa\x00\xe7\x92\x1am\x10\x01'
            b'\x15\xbd\xb5\x0b|6@1\xdc6\xd4\xded5\xb8\xd8%\xc0\x00\xca\xfa\xbb\xa9d\x08\xbc*\xf4\x8b\xc3\xf2\xb2pAAL8'
            b'\xc4\xe8\x87\x92\xb9\x1f7\xb3\xba0;V\xb8\xff\xba\x00\x014\x94\xcdkq\x00\xff\xba\x80\xae\x99:|\x8d\xcb\xb9'
            b'\xa5\xc0\xd1\xba\x89\x9e$\xc0\x00\x19\x00\xbc\xd2\xdcb\xbb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00'
        )
        self.m_expected_json_23_24_25 = {
            "car-motion-data": [
                {
                    "world-position": {
                        "x": -271.3988037109375,
                        "y": 14.724800109863281,
                        "z": -723.61767578125
                    },
                    "world-velocity": {
                        "x": 0.0001811655383789912,
                        "y": -0.0009959058370441198,
                        "z": -0.0006909227231517434
                    },
                    "world-forward-dir": {
                        "x": -17666,
                        "y": 258,
                        "z": -27595
                    },
                    "world-right-dir": {
                        "x": 27596,
                        "y": 200,
                        "z": -17665
                    },
                    "g-force": {
                        "lateral": 7.5122088674106635e-06,
                        "longitudinal": 9.615591807232704e-06,
                        "vertical": -1.4028184523340315e-05
                    },
                    "orientation": {
                        "yaw": -2.572145938873291,
                        "pitch": -0.007882237434387207,
                        "roll": -0.006111640017479658
                    }
                },
                {
                    "world-position": {
                        "x": -294.83990478515625,
                        "y": 15.813430786132812,
                        "z": -775.1607055664062
                    },
                    "world-velocity": {
                        "x": 0.0020830449648201466,
                        "y": -0.00048391989548690617,
                        "z": 0.003561489749699831
                    },
                    "world-forward-dir": {
                        "x": -17503,
                        "y": 210,
                        "z": -27699
                    },
                    "world-right-dir": {
                        "x": 27699,
                        "y": -120,
                        "z": -17504
                    },
                    "g-force": {
                        "lateral": 8.316955586451513e-07,
                        "longitudinal": 2.557215793785872e-06,
                        "vertical": 4.130475645069964e-06
                    },
                    "orientation": {
                        "yaw": -2.578047513961792,
                        "pitch": -0.006417632102966309,
                        "roll": 0.003677475033327937
                    }
                },
                {
                    "world-position": {
                        "x": -277.6441650390625,
                        "y": 15.216286659240723,
                        "z": -748.0677490234375
                    },
                    "world-velocity": {
                        "x": -0.00021773733897134662,
                        "y": -0.0012141717597842216,
                        "z": -0.0003344487049616873
                    },
                    "world-forward-dir": {
                        "x": -17506,
                        "y": 212,
                        "z": -27697
                    },
                    "world-right-dir": {
                        "x": 27698,
                        "y": 61,
                        "z": -17506
                    },
                    "g-force": {
                        "lateral": 1.8318141883355565e-06,
                        "longitudinal": -2.2288404579740018e-05,
                        "vertical": -2.666983345989138e-05
                    },
                    "orientation": {
                        "yaw": -2.5779449939727783,
                        "pitch": -0.006500244140625,
                        "roll": -0.0018727554706856608
                    }
                },
                {
                    "world-position": {
                        "x": -269.22894287109375,
                        "y": 14.920071601867676,
                        "z": -734.4841918945312
                    },
                    "world-velocity": {
                        "x": 0.0008806310361251235,
                        "y": -0.0010839075548574328,
                        "z": 0.00235572992824018
                    },
                    "world-forward-dir": {
                        "x": -17508,
                        "y": 204,
                        "z": -27696
                    },
                    "world-right-dir": {
                        "x": 27696,
                        "y": 149,
                        "z": -17508
                    },
                    "g-force": {
                        "lateral": -1.5383033314719796e-05,
                        "longitudinal": -2.8820892111980356e-05,
                        "vertical": 3.0473120204987936e-05
                    },
                    "orientation": {
                        "yaw": -2.5778558254241943,
                        "pitch": -0.006239414215087891,
                        "roll": -0.004569613840430975
                    }
                },
                {
                    "world-position": {
                        "x": -260.96307373046875,
                        "y": 14.621031761169434,
                        "z": -720.7604370117188
                    },
                    "world-velocity": {
                        "x": 0.0014889875892549753,
                        "y": -0.0007167531875893474,
                        "z": -0.000979201984591782
                    },
                    "world-forward-dir": {
                        "x": -17345,
                        "y": 214,
                        "z": -27798
                    },
                    "world-right-dir": {
                        "x": 27799,
                        "y": 256,
                        "z": -17344
                    },
                    "g-force": {
                        "lateral": -4.636412995751016e-06,
                        "longitudinal": 1.948326826095581e-06,
                        "vertical": 5.365423476177966e-06
                    },
                    "orientation": {
                        "yaw": -2.5837290287017822,
                        "pitch": -0.006556272506713867,
                        "roll": -0.007826276123523712
                    }
                },
                {
                    "world-position": {
                        "x": -288.3892822265625,
                        "y": 15.362330436706543,
                        "z": -750.8480834960938
                    },
                    "world-velocity": {
                        "x": 0.0011063417186960578,
                        "y": -0.001027956954203546,
                        "z": 0.002392940688878298
                    },
                    "world-forward-dir": {
                        "x": -17508,
                        "y": 244,
                        "z": -27696
                    },
                    "world-right-dir": {
                        "x": 27696,
                        "y": 44,
                        "z": -17508
                    },
                    "g-force": {
                        "lateral": 8.564957170165144e-06,
                        "longitudinal": 2.0009327272418886e-05,
                        "vertical": -1.2826914826291613e-05
                    },
                    "orientation": {
                        "yaw": -2.5778591632843018,
                        "pitch": -0.007453441619873047,
                        "roll": -0.0013429997488856316
                    }
                },
                {
                    "world-position": {
                        "x": -296.94158935546875,
                        "y": 15.676932334899902,
                        "z": -764.3612060546875
                    },
                    "world-velocity": {
                        "x": 0.0009466999908909202,
                        "y": -0.001161755295470357,
                        "z": 0.002557802712544799
                    },
                    "world-forward-dir": {
                        "x": -17666,
                        "y": 235,
                        "z": -27595
                    },
                    "world-right-dir": {
                        "x": 27595,
                        "y": 3,
                        "z": -17667
                    },
                    "g-force": {
                        "lateral": -7.607199677295284e-06,
                        "longitudinal": -1.633772990317084e-05,
                        "vertical": 2.1705568542529363e-06
                    },
                    "orientation": {
                        "yaw": -2.572124719619751,
                        "pitch": -0.007173299789428711,
                        "roll": -0.00011423605610616505
                    }
                },
                {
                    "world-position": {
                        "x": -286.2794189453125,
                        "y": 15.514098167419434,
                        "z": -761.5968627929688
                    },
                    "world-velocity": {
                        "x": -0.000224844814511016,
                        "y": -0.0015412146458402276,
                        "z": -0.0002784257521852851
                    },
                    "world-forward-dir": {
                        "x": -17823,
                        "y": 219,
                        "z": -27494
                    },
                    "world-right-dir": {
                        "x": 27494,
                        "y": -23,
                        "z": -17824
                    },
                    "g-force": {
                        "lateral": 2.080136027871049e-06,
                        "longitudinal": 4.6678695753143984e-07,
                        "vertical": 1.215783299812756e-06
                    },
                    "orientation": {
                        "yaw": -2.5664381980895996,
                        "pitch": -0.0066939592361450195,
                        "roll": 0.0007318826974369586
                    }
                },
                {
                    "world-position": {
                        "x": -262.5788269042969,
                        "y": 14.41189956665039,
                        "z": -710.2549438476562
                    },
                    "world-velocity": {
                        "x": -0.0003039030125364661,
                        "y": 0.0009606075473129749,
                        "z": -0.0009221683721989393
                    },
                    "world-forward-dir": {
                        "x": -17133,
                        "y": 250,
                        "z": -27929
                    },
                    "world-right-dir": {
                        "x": 27930,
                        "y": 272,
                        "z": -17131
                    },
                    "g-force": {
                        "lateral": 3.7557740597549127e-06,
                        "longitudinal": 6.562244379892945e-06,
                        "vertical": 8.526087640348123e-07
                    },
                    "orientation": {
                        "yaw": -2.5913524627685547,
                        "pitch": -0.007653474807739258,
                        "roll": -0.008324780501425266
                    }
                },
                {
                    "world-position": {
                        "x": -279.90753173828125,
                        "y": 15.04368782043457,
                        "z": -737.1914672851562
                    },
                    "world-velocity": {
                        "x": -0.0002794854808598757,
                        "y": -0.0013673043577000499,
                        "z": -5.107669858261943e-05
                    },
                    "world-forward-dir": {
                        "x": -17665,
                        "y": 256,
                        "z": -27596
                    },
                    "world-right-dir": {
                        "x": 27597,
                        "y": 113,
                        "z": -17665
                    },
                    "g-force": {
                        "lateral": 0.0011724978685379028,
                        "longitudinal": -0.0003882459132000804,
                        "vertical": -0.001600284711457789
                    },
                    "orientation": {
                        "yaw": -2.572176218032837,
                        "pitch": -0.007818460464477539,
                        "roll": -0.0034616482444107533
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                },
                {
                    "world-position": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-velocity": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "world-forward-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "world-right-dir": {
                        "x": 0,
                        "y": 0,
                        "z": 0
                    },
                    "g-force": {
                        "lateral": 0.0,
                        "longitudinal": 0.0,
                        "vertical": 0.0
                    },
                    "orientation": {
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0
                    }
                }
            ]
        }

    def test_f1_23_random(self):
        """
        Test for F1 2023 with randomly generated data
        """

        # First, generate the random PacketMotionData object and serialise it
        car_motion_objects = (
            [self._generateRandomCarMotionData() for _ in range(self.m_num_players)] +
            [self._generateEmptyCarMotionData() for _ in range(self.m_num_players, PacketMotionData.MAX_CARS)]
        )
        generated_test_obj = PacketMotionData.from_values(self.m_header_23, car_motion_objects)
        serialised_test_obj = generated_test_obj.to_bytes()

        # Extract the header and parse it
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)

        # Extract the payload, parse and test it
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketMotionData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())
        self.assertFalse(hasattr(parsed_obj, '__dict__'))

    def test_f1_24_random(self):
        """
        Test for F1 2024 with randomly generated data
        """

        # First, generate the random PacketMotionData object and serialise it
        car_motion_objects = (
            [self._generateRandomCarMotionData() for _ in range(self.m_num_players)] +
            [self._generateEmptyCarMotionData() for _ in range(self.m_num_players, PacketMotionData.MAX_CARS)]
        )
        generated_test_obj = PacketMotionData.from_values(self.m_header_24, car_motion_objects)
        serialised_test_obj = generated_test_obj.to_bytes()

        # Extract the header and parse it
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)

        # Extract the payload, parse and test it
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketMotionData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())
        self.assertFalse(hasattr(parsed_obj, '__dict__'))

    def test_f1_25_random(self):
        """
        Test for F1 2025 with randomly generated data
        """

        # First, generate the random PacketMotionData object and serialise it
        car_motion_objects = (
            [self._generateRandomCarMotionData() for _ in range(self.m_num_players)] +
            [self._generateEmptyCarMotionData() for _ in range(self.m_num_players, PacketMotionData.MAX_CARS)]
        )
        generated_test_obj = PacketMotionData.from_values(self.m_header_25, car_motion_objects)
        serialised_test_obj = generated_test_obj.to_bytes()

        # Extract the header and parse it
        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)

        # Extract the payload, parse and test it
        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketMotionData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())
        self.assertFalse(hasattr(parsed_obj, '__dict__'))

    def test_f1_23_actual(self):
        """
        Test for F1 2023 with an actual game packet
        """

        parsed_packet = PacketMotionData(self.m_header_23, self.m_packet_23_24_25)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(self.m_expected_json_23_24_25, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        parsed_packet = PacketMotionData(self.m_header_24, self.m_packet_23_24_25)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(self.m_expected_json_23_24_25, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_25_actual(self):
        """
        Test for F1 2025 with an actual game packet
        """

        parsed_packet = PacketMotionData(self.m_header_25, self.m_packet_23_24_25)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(self.m_expected_json_23_24_25, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def _generateRandomCarMotionData(self) -> CarMotionData:
        """Generate a random CarMotionData object

        Returns:
            CarMotionData: The generated CarMotionData object
        """
        return CarMotionData.from_values(
            world_position_x=random.uniform(-100.0, 100.0),
            world_position_y=random.uniform(-100.0, 100.0),
            world_position_z=random.uniform(-100.0, 100.0),
            world_velocity_x=random.uniform(-50.0, 50.0),
            world_velocity_y=random.uniform(-50.0, 50.0),
            world_velocity_z=random.uniform(-50.0, 50.0),
            world_forward_dir_x=random.randint(-1000, 1000),
            world_forward_dir_y=random.randint(-1000, 1000),
            world_forward_dir_z=random.randint(-1000, 1000),
            world_right_dir_x=random.randint(-1000, 1000),
            world_right_dir_y=random.randint(-1000, 1000),
            world_right_dir_z=random.randint(-1000, 1000),
            g_force_lateral=random.uniform(-10.0, 10.0),
            g_force_longitudinal=random.uniform(-10.0, 10.0),
            g_force_vertical=random.uniform(-10.0, 10.0),
            yaw=random.uniform(-3.14, 3.14),
            pitch=random.uniform(-3.14, 3.14),
            roll=random.uniform(-3.14, 3.14)
        )

    def _generateEmptyCarMotionData(self, packet_format: int = 0) -> CarMotionData:
        """Generate a car motion data object with all zeroes

        Returns:
            CarMotionData: Generated object
        """
        return CarMotionData.from_values(
            world_position_x=0.0,
            world_position_y=0.0,
            world_position_z=0.0,
            world_velocity_x=0.0,
            world_velocity_y=0.0,
            world_velocity_z=0.0,
            world_forward_dir_x=0,
            world_forward_dir_y=0,
            world_forward_dir_z=0,
            world_right_dir_x=0,
            world_right_dir_y=0,
            world_right_dir_z=0,
            g_force_lateral=0.0,
            g_force_longitudinal=0.0,
            g_force_vertical=0.0,
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            packet_format=packet_format,
        )

    def _generateRandomCarMotionData_26(self) -> CarMotionData:
        """Generate a random CarMotionData object for F1 26 format.

        G-force values are integer/1000.0 to survive the int16 quantization round-trip.

        Returns:
            CarMotionData: The generated CarMotionData object
        """
        return CarMotionData.from_values(
            world_position_x=random.uniform(-100.0, 100.0),
            world_position_y=random.uniform(-100.0, 100.0),
            world_position_z=random.uniform(-100.0, 100.0),
            world_velocity_x=random.uniform(-50.0, 50.0),
            world_velocity_y=random.uniform(-50.0, 50.0),
            world_velocity_z=random.uniform(-50.0, 50.0),
            world_forward_dir_x=random.randint(-1000, 1000),
            world_forward_dir_y=random.randint(-1000, 1000),
            world_forward_dir_z=random.randint(-1000, 1000),
            world_right_dir_x=random.randint(-1000, 1000),
            world_right_dir_y=random.randint(-1000, 1000),
            world_right_dir_z=random.randint(-1000, 1000),
            g_force_lateral=random.randint(-32767, 32767) / 1000.0,
            g_force_longitudinal=random.randint(-32767, 32767) / 1000.0,
            g_force_vertical=random.randint(-32767, 32767) / 1000.0,
            yaw=random.uniform(-3.14, 3.14),
            pitch=random.uniform(-3.14, 3.14),
            roll=random.uniform(-3.14, 3.14),
            packet_format=2026,
        )

    def test_f1_26_random(self):
        """Test for F1 2026 with randomly generated data (24 cars, int16 g-forces)."""

        car_motion_objects = (
            [self._generateRandomCarMotionData_26() for _ in range(self.m_num_players_26)] +
            [self._generateEmptyCarMotionData(packet_format=2026)
             for _ in range(self.m_num_players_26, PacketMotionData.MAX_CARS_2026)]
        )
        generated_test_obj = PacketMotionData.from_values(self.m_header_26, car_motion_objects)
        serialised_test_obj = generated_test_obj.to_bytes()

        header_bytes = serialised_test_obj[:PacketHeader.PACKET_LEN]
        parsed_header = PacketHeader(header_bytes)

        payload_bytes = serialised_test_obj[PacketHeader.PACKET_LEN:]
        parsed_obj = PacketMotionData(parsed_header, payload_bytes)
        self.assertEqual(generated_test_obj, parsed_obj)
        self.assertEqual(len(parsed_obj.m_carMotionData), 24)
        self.jsonComparisionUtil(generated_test_obj.toJSON(), parsed_obj.toJSON())
        self.assertFalse(hasattr(parsed_obj, '__dict__'))

    def test_f1_26_actual(self):
        """Test for F1 2026 with an actual game packet."""
        raw_packet = b'h\x93\xa1\xc3F>\xd5\xbf\xf8bbC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x80\xec\x12<\xcb\x01\xae3tV\xb3\xc3@\xfc\xd1\xbf\xcb\xb9\x8bC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xfa\xc1?\xb4c_\xa5\xc3\xdf\xde\xd1\xbf\xda\xbamC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x80\xec\x12<\xbb\x01(\xb4\x9d\x8a\xaf\xc3\xfa\x08\xd2\xbf\x12\x0e\x86C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xab\x01\xa2\xb2,\x05\x9c\xc3\xdb\xc9\xd2\xbf\xee\xc9QC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xd3A14\xb37\xe9\xc3\x818\xfe\xbf\xafv\x08D\xa6Y\xe9\xc1|\x8d\xa7\xbe\x0cV\xd9\xc1\xb3\xa4\xad\xfeO\xa6\xafY/\x01\xb1\xa4\xa7\xf7\xc4\x02A\x00u:\x16\xc0\x00\xd9)<\xec\xee\x17\xbc\x8b\xc7\x9d\xc3\'\x18\xd1\xbfx\x0bWC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x00\xed\x12<\xc8\x01-47\xba\xbe\xc3\x9b)\xd2\xbfP\xbd\x9cC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\x8cA\x164!\xd1\x9f\xc3&\x18\xd1\xbf\xbd!]C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xe3\x01\xb73\xa1\xb0\xbc\xc3\x9b)\xd2\xbf,\xb2\x99C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x80\xec\x12<R\x01\x001\x9d:\x98\xc3iN\xd5\xbffvFC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xd3A14\xdf\xb8\x8b\xc3-"\x8f@r\xd6\xfc\xc3\x93N\xc1\xc127%>B\xd6\x80A\xb9\x95\x8b\xffTG\xb0\xb8\xd7\xfd\xbc\x95m\xf8`\xfe\xf0\xff\x0f\xcdz\xbf\x00\xb8k;\x9fs\x8a<\xa2h\xa7\xc3\xea\x06\xd2\xbf\x94\xd1sC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xcbA\xae4,\xee\xba\xc3\x97\x1c\xd1\xbfL\x11\x97C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xf9\x81?\xb43\xe7\x87\xc34\xe5\x8c@\x8d\x07\x00\xc4PO\xa7\xc1\xec\xaa\x81>\xf5\x10\xb2AL\xa8\xd2\xff9]\xc9\xa2Z\xfeM\xa8\xff\xf7h\xfd\xfd\xffZAA\xbf\x00\x14\xb9:q(S<\x93\xa3\x8f\xc3\x19\xfe\xd0\xbf\x98\xcc,C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<\xd3A14\x16\x92\xf1\xc34\xa3Z\xc0]\x8a\xbaC\xacK\x00B\xb7A\x0b\xbd(\xb8[\xc2MB\xdc\xff\x84\x92|m7\x00MB\xd9\xf7\xbd\x01(\x00z6&@\x00X\x92:N\xe2\xdd\xba\xdeL\xb1\xc3@\xfc\xd1\xbf\xa7\xae\x88C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x80\xec\x12<\xb6\x01\xa6\xb3\x96\xfb\x99\xc3\xdb\xc9\xd2\xbf\xa9\xb3KC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x80\xec\x12<\xc8\x01-4\x96\xe4\xb8\xc3\x97\x1c\xd1\xbf(\x06\x94C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe9\x95\xdb\xfeh\xb8\x99G\x00\x00\xe8\x95\x00\x00\x00\x00\x00\x00A\x86\n\xc0\x80\xec\x12<\xc8\x01-4\xfe\x9c\xa3\xc3E>\xd5\xbf=yhC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00a\x95\xdb\xfe3\xb9\xceF\x00\x00`\x95\x00\x00\x00\x00\x00\x00$\x0c\n\xc0\x80\xec\x12<[\xa1\x8340cKC\x99\xfc\xb2?}/\xefC\x08-\xe0\xc1\xa96\xbc\xbe@E;B\xd6\xbdT\xfe\x8dmt\x92\xa8\xfe\xd1\xbdm\xfe\x01\xfe\x85\x01\xe7\x17\x0b\xbf\x00\x83V<`\x10,<\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {'car-motion-data': [{'world-position': {'x': -323.151611328125, 'y': -1.6659629344940186, 'z': 226.3865966796875}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896751880645752, 'roll': 8.102832538270377e-08}}, {'world-position': {'x': -358.6754150390625, 'y': -1.6405105590820312, 'z': 279.4515075683594}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': -1.785882943750039e-07}}, {'world-position': {'x': -330.7452087402344, 'y': -1.6396139860153198, 'z': 237.72988891601562}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896751880645752, 'roll': -1.5646848794403923e-07}}, {'world-position': {'x': -351.0829162597656, 'y': -1.6408989429473877, 'z': 268.10992431640625}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': -1.8860040640333864e-08}}, {'world-position': {'x': -312.0404052734375, 'y': -1.6467851400375366, 'z': 209.78878784179688}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 1.6508356281974557e-07}}, {'world-position': {'x': -466.4351501464844, 'y': -1.986099362373352, 'z': 545.8544311523438}, 'world-velocity': {'x': -29.168773651123047, 'y': -0.3272513151168823, 'z': -27.167015075683594}, 'world-forward-dir': {'x': -23373, 'y': -339, 'z': -22961}, 'world-right-dir': {'x': 22959, 'y': 303, 'z': -23375}, 'g-force': {'lateral': -2.137, 'longitudinal': 0.708, 'vertical': 0.065}, 'orientation': {'yaw': -2.347317934036255, 'pitch': 0.010366678237915039, 'roll': -0.009273272007703781}}, {'world-position': {'x': -315.5589294433594, 'y': -1.6335495710372925, 'z': 215.0447998046875}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896763801574707, 'roll': 1.6112528555822792e-07}}, {'world-position': {'x': -381.4548034667969, 'y': -1.6418946981430054, 'z': 313.47900390625}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 1.3993684433444287e-07}}, {'world-position': {'x': -319.6338195800781, 'y': -1.633549451828003, 'z': 221.1317901611328}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 8.521944749873e-08}}, {'world-position': {'x': -377.3799133300781, 'y': -1.6418946981430054, 'z': 307.3919677734375}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896751880645752, 'roll': 1.8627202003074217e-09}}, {'world-position': {'x': -304.4579162597656, 'y': -1.6664553880691528, 'z': 198.46249389648438}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 1.6508356281974557e-07}}, {'world-position': {'x': -279.4443054199219, 'y': 4.472921848297119, 'z': -505.67535400390625}, 'world-velocity': {'x': -24.163366317749023, 'y': 0.16134336590766907, 'z': 16.104618072509766}, 'world-forward-dir': {'x': -27207, 'y': -117, 'z': 18260}, 'world-right-dir': {'x': -18256, 'y': -553, 'z': -27204}, 'g-force': {'lateral': -1.939, 'longitudinal': -0.416, 'vertical': -0.016}, 'orientation': {'yaw': -0.9796914458274841, 'pitch': 0.003596782684326172, 'roll': 0.016900835558772087}}, {'world-position': {'x': -334.81744384765625, 'y': -1.6408360004425049, 'z': 243.81866455078125}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 3.245789628181228e-07}}, {'world-position': {'x': -373.8607177734375, 'y': -1.6336849927902222, 'z': 302.1351318359375}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': -1.783554495204953e-07}}, {'world-position': {'x': -271.8062438964844, 'y': 4.402978897094727, 'z': -512.1179809570312}, 'world-velocity': {'x': -20.913726806640625, 'y': 0.253257155418396, 'z': 22.25827980041504}, 'world-forward-dir': {'x': -22452, 'y': -46, 'z': 23865}, 'world-right-dir': {'x': -23863, 'y': -422, 'z': -22451}, 'g-force': {'lateral': -2.049, 'longitudinal': -0.664, 'vertical': -0.003}, 'orientation': {'yaw': -0.7549034357070923, 'pitch': 0.001412034034729004, 'roll': 0.012888059951364994}}, {'world-position': {'x': -287.2779235839844, 'y': -1.6327544450759888, 'z': 172.7991943359375}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 1.6508356281974557e-07}}, {'world-position': {'x': -483.14129638671875, 'y': -3.4162111282348633, 'z': 373.0809631347656}, 'world-velocity': {'x': 32.07389831542969, 'y': -0.033998217433691025, 'z': -54.929840087890625}, 'world-forward-dir': {'x': 16973, 'y': -36, 'z': -28028}, 'world-right-dir': {'x': 28028, 'y': 55, 'z': 16973}, 'g-force': {'lateral': -2.087, 'longitudinal': 0.445, 'vertical': 0.04}, 'orientation': {'yaw': 2.5970749855041504, 'pitch': 0.0011165142059326172, 'roll': -0.0016928405966609716}}, {'world-position': {'x': -354.60052490234375, 'y': -1.6405105590820312, 'z': 273.3644714355469}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896751880645752, 'roll': -7.730288587026735e-08}}, {'world-position': {'x': -307.96551513671875, 'y': -1.6467851400375366, 'z': 203.70179748535156}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896751880645752, 'roll': 1.6112528555822792e-07}}, {'world-position': {'x': -369.78582763671875, 'y': -1.6336849927902222, 'z': 296.048095703125}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27159, 'y': -293, 'z': -18328}, 'world-right-dir': {'x': 18329, 'y': 0, 'z': -27160}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1644442081451416, 'pitch': 0.00896751880645752, 'roll': 1.6112528555822792e-07}}, {'world-position': {'x': -327.22650146484375, 'y': -1.665962815284729, 'z': 232.4735870361328}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': -27295, 'y': -293, 'z': -18125}, 'world-right-dir': {'x': 18126, 'y': 0, 'z': -27296}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': -2.1569910049438477, 'pitch': 0.00896751880645752, 'roll': 2.4518053010069707e-07}}, {'world-position': {'x': 203.387451171875, 'y': 1.3983336687088013, 'z': 478.3710021972656}, 'world-velocity': {'x': -28.021987915039062, 'y': -0.367604523897171, 'z': 46.817626953125}, 'world-forward-dir': {'x': -16938, 'y': -428, 'z': 28045}, 'world-right-dir': {'x': -28044, 'y': -344, 'z': -16943}, 'g-force': {'lateral': -0.403, 'longitudinal': -0.511, 'vertical': 0.389}, 'orientation': {'yaw': -0.5433334708213806, 'pitch': 0.013092756271362305, 'roll': 0.010501950979232788}}, {'world-position': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': 0, 'y': 0, 'z': 0}, 'world-right-dir': {'x': 0, 'y': 0, 'z': 0}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0}}, {'world-position': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'world-forward-dir': {'x': 0, 'y': 0, 'z': 0}, 'world-right-dir': {'x': 0, 'y': 0, 'z': 0}, 'g-force': {'lateral': 0.0, 'longitudinal': 0.0, 'vertical': 0.0}, 'orientation': {'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0}}]}
        parsed_packet = PacketMotionData(self.m_header_26, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))
