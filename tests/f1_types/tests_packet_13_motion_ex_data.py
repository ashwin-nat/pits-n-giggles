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

from lib.f1_types import PacketMotionExData, F1PacketType
from .tests_parser_base import F1TypesTest

class TestPacketMotionExData(F1TypesTest):
    """
    Tests for TestPacketMotionExData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = 22
        self.m_header_23 = F1TypesTest.getRandomHeader(F1PacketType.MOTION_EX, 23, self.m_num_players)
        self.m_header_24 = F1TypesTest.getRandomHeader(F1PacketType.MOTION_EX, 24, self.m_num_players)
        self.m_header_25 = F1TypesTest.getRandomHeader(F1PacketType.MOTION_EX, 25, self.m_num_players)
        self.m_header_26 = F1TypesTest.getRandomHeader(F1PacketType.MOTION_EX, 26, 24)

    def test_f1_23_actual(self) -> None:
        """
        Test the actual data
        """

        raw_packet = b'\xbb\r;B$\xbb;B\xa49AB\xef\xa4ABrz\x03\xc0\xde\x02\xf0?\xdd\x11\xf1\xbf[3\xe8?\xe1\xe4\x9d\xc6\x98\x97\x9a\xc6\x18Q\x92\xc7,\xe2\x91\xc7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x823M\xb8\x90\x08\x17\xb8)JO\xb8\x9d\x16\x15\xb8(.\r8u\x9c\x0b8T\rl6\x867q6%\xa6jB\x18S]BW\x9e]B\xc9EcB\x9a\xb0\x17\xc1\xf5R\xed\xbe{f\x12\xc1\x86\x00\t\xc1\x80\x87\xc8=.P\x9a7\xd1\x06\x1c:FQ\xba9z\xa0\x00<\x9f\xc0\x1b9]\x96\xee\xba\xe4,\xf1>\x94\x04\x12<\xf6\xac\xdf\xbd\x00\x00\x00\x80\x8ac\x0eER\x95\x13E\x9d\xad\x04E\x17\xaf\x08E'
        expected_json = {
            "suspension-position": [
                46.76340866088867,
                46.93275451660156,
                48.30628967285156,
                48.411067962646484
            ],
            "suspension-velocity": [
                -2.0543484687805176,
                1.8750874996185303,
                -1.8833576440811157,
                1.8140672445297241
            ],
            "suspension-acceleration": [
                -20210.439453125,
                -19787.796875,
                -74914.1875,
                -74692.34375
            ],
            "wheel-speed": [
                0.0,
                0.0,
                0.0,
                0.0
            ],
            "wheel-slip-ratio": [
                -4.8923779104370624e-05,
                -3.600917989388108e-05,
                -4.9421712901676074e-05,
                -3.5545428545447066e-05
            ],
            "wheel-slip-angle": [
                3.366000601090491e-05,
                3.328589446027763e-05,
                3.517449840728659e-06,
                3.5944117371400353e-06
            ],
            "wheel-lat-force": [
                58.66225051879883,
                55.331146240234375,
                55.40462875366211,
                56.81814956665039
            ],
            "wheel-long-force": [
                -9.480615615844727,
                -0.4635235369205475,
                -9.150019645690918,
                -8.562627792358398
            ],
            "height-of-cog-above-ground": 0.0979146957397461,
            "local-velocity": {
                "x": 1.8395567167317495e-05,
                "y": 0.000595194345805794,
                "z": 0.0003553723799996078
            },
            "angular-velocity": {
                "x": 0.007850760594010353,
                "y": 0.00014853708853479475,
                "z": -0.0018202770734205842
            },
            "angular-acceleration": {
                "x": 0.4710456132888794,
                "y": 0.00891222432255745,
                "z": -0.1092166155576706
            },
            "front-wheels-angle": -0.0,
            "wheel-vert-force": [
                2278.22119140625,
                2361.33251953125,
                2122.850830078125,
                2186.943115234375
            ],
            "front-aero-height": 0.0,
            "rear-aero-height": 0.0,
            "front-roll-angle": 0.0,
            "rear-roll-angle": 0.0,
            "chassis-yaw": 0.0,
            "chassis-pitch": 0.0,
            "wheel-camber" : [
                0.0,
                0.0,
                0.0,
                0.0
            ],
            "wheel-camber-gain": [
                0.0,
                0.0,
                0.0,
                0.0
            ],
        }

        parsed_packet = PacketMotionExData(self.m_header_23, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_24_actual(self):
        """
        Test for F1 2024 with an actual game packet
        """

        raw_packet = b'4\xc9\xe5@\xb0+\xd6@E/XB\xca1XB\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb6=\xb8\xc2+ \xe0A\x90m_\xc2\x88"\x98A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf9\xfem\xb9\xf5\x19\x85\xb9H\xf0o\xb9\xd8\xfe\x84\xb9c>\xd89s[\xd79\xbd\x98\xb79z\xb9\xb79A\xadX\xc0\x1f\xc2\x84\xc2J8\xe0\xc2-\x11!B%\x81\xa4B]\x16\x91B\x1a\x04\xf1\xc1\xee\x15!\xc2\x803\xae>\x00IA;\x83z:\xbb(\x91{9^T\x00\xbb\t\xb1\xa3:B\xfe\xf2:r\xd0h<\xa3k\x95\xba\x8a\x8bJ\xbd\x00\x00\x00\x80\xbf("E\x1c7\x1eE\xa3[\x06E0\x08\x07E\xc8\xb3\xdd<\xc2\xfdu=X\xcb\xcc\xb5w\xf6\xa59\x00\x00\x00\x00'
        expected_json = {
            "suspension-position": [
                7.180810928344727,
                6.692832946777344,
                54.04616165161133,
                54.048622131347656
            ],
            "suspension-velocity": [
                0.0,
                0.0,
                0.0,
                0.0
            ],
            "suspension-acceleration": [
                -92.12052917480469,
                28.01570701599121,
                -55.85699462890625,
                19.016860961914062
            ],
            "wheel-speed": [
                0.0,
                0.0,
                0.0,
                0.0
            ],
            "wheel-slip-ratio": [
                -0.00022697066015098244,
                -0.0002538707631174475,
                -0.00022882327903062105,
                -0.0002536687534302473
            ],
            "wheel-slip-angle": [
                0.0004124521219637245,
                0.0004107613058295101,
                0.00035018278867937624,
                0.00035042670788243413
            ],
            "wheel-lat-force": [
                -3.3855745792388916,
                -66.37914276123047,
                -112.10993957519531,
                40.26677322387695
            ],
            "wheel-long-force": [
                82.25223541259766,
                72.5436782836914,
                -30.127002716064453,
                -40.27141571044922
            ],
            "height-of-cog-above-ground": 0.3402366638183594,
            "local-velocity": {
                "x": 0.0029492974281311035,
                "y": -0.0028454370331019163,
                "z": 0.00023991300258785486
            },
            "angular-velocity": {
                "x": -0.0019581536762416363,
                "y": 0.0012488673673942685,
                "z": 0.0018538909498602152
            },
            "angular-acceleration": {
                "x": 0.014209853485226631,
                "y": -0.0011399876093491912,
                "z": -0.049449481070041656
            },
            "front-wheels-angle": -0.0,
            "wheel-vert-force": [
                2594.546630859375,
                2531.4443359375,
                2149.727294921875,
                2160.51171875
            ],
            "front-aero-height": 0.027063265442848206,
            "rear-aero-height": 0.06005645543336868,
            "front-roll-angle": -1.5258365237968974e-06,
            "rear-roll-angle": 0.0003165488305967301,
            "chassis-yaw": 0.0,
            "chassis-pitch": 0.0,
            "wheel-camber" : [
                0.0,
                0.0,
                0.0,
                0.0
            ],
            "wheel-camber-gain": [
                0.0,
                0.0,
                0.0,
                0.0
            ],
        }

        parsed_packet = PacketMotionExData(self.m_header_24, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_25_actual(self):
        """
        Test for F1 2025 with an actual game packet
        """

        raw_packet = b'\xb4A\xf3A\xde\xfc\x00B\xa7\x89WB#\x10TB\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\xf1\xe2\xc3:k\x9dB\xf0\x18RC9\x89!C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00e\xd1\x98\xb9d\xf3\x91\xb9k\xa2\x99\xb9\xd8C\x92\xb9\xeb\x14\x868\x10\x0b\x858=(\xa88\xb9\xf9\xa78ku\x08\xc3\x10\xc4\x88\xc2\x07\x8a\xfb\xc29|\xcb\xc1\x16\x83\xd0\xc1\x89\xd40\xc1\x90@3\xc2\xd0]\xc7\xc1\x80S\x9b>o\xc5\xf9\xba\x8c\xbdy;|^\x8d9\x18\xb9\xe7\xba\xb5\x86\x9a\xb8S\xef\xa0:\xc5z\xc6>\xa9R!\xbe\x8c\xcb\xc4\xbd\x00\x00\x00\x80\xb4K\x00E\x8a\x91\x14E\xcf\xcb\x00E\xec\xcd\xc3D \xa4\xe6<\xa7\x931=W\x12\r:\x8aF\x9c\xba\x00\x00\x00\x80\x00\xcc\xc1;\x06/\xfa\xbc\x06/\xfa\xbcpwV\xbdpwV\xbd82\x8f;82\x8f;\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {"suspension-position": [30.407081604003906, 32.24694061279297, 53.88442611694336, 53.0157585144043], "suspension-velocity": [0.0, 0.0, 0.0, 0.0], "suspension-acceleration": [-453.8834228515625, 78.70942687988281, 210.097412109375, 161.53602600097656], "wheel-speed": [0.0, 0.0, 0.0, 0.0], "wheel-slip-ratio": [-0.0002914771030191332, -0.00027837895322591066, -0.00029303444898687303, -0.00027897837571799755], "wheel-slip-angle": [6.39351419522427e-05, 6.343994755297899e-05, 8.01835922175087e-05, 8.009695011423901e-05], "wheel-lat-force": [-136.4586639404297, -68.3829345703125, -125.76958465576172, -25.43565559387207], "wheel-long-force": [-26.064006805419922, -11.051888465881348, -44.81304931640625, -24.920806884765625], "height-of-cog-above-ground": 0.3033714294433594, "local-velocity": {"x": -0.0019056032178923488, "y": 0.0038107363507151604, "z": 0.00026964012067765}, "angular-velocity": {"x": -0.0017679063603281975, "y": -7.368383376160637e-05, "z": 0.0012278355425223708}, "angular-acceleration": {"x": 0.3876554071903229, "y": -0.157541885972023, "z": -0.0960913598537445}, "front-wheels-angle": -0.0, "wheel-vert-force": [2052.7314453125, 2377.09619140625, 2060.738037109375, 1566.43505859375], "front-aero-height": 0.028154432773590088, "rear-aero-height": 0.04335370287299156, "front-roll-angle": 0.0005381455994211137, "rear-roll-angle": -0.0011922877747565508, "chassis-yaw": -0.0, "chassis-pitch": 0.005914211273193359, "wheel-camber": [-0.030540000647306442, -0.030540000647306442, -0.05235999822616577, -0.05235999822616577], "wheel-camber-gain": [0.004370000213384628, 0.004370000213384628, 0.0, 0.0]}

        parsed_packet = PacketMotionExData(self.m_header_25, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_26_actual(self):
        """
        Test for F1 2026 with an actual game packet
        """

        raw_packet = b'$\xe5IA\x7f\xb8JA\x9f\xec8B}\xef:B\xc7i{\xc1\xb9E\x86A\xee\x1b\x19\xc1\x18\xabNA\xf3\xb4y\xc4\x7f\x95uD!#\xda\xc35\xd0MD"\xbe7A\xda\xf98AU\x9c7A\x9309A\x07R\\:\xd1\xafI\xba\xd5Z\xf88\xc6\x17\xb3\xb8\xe7\xed\xb0:K\xc4w\xbb!F\x10\xbb\xc5\xd0+\xbb2\xcc\x97\xc3<%5D\xd8;\xf3B\xa8x\xe0CUK\xc3B\xdb@\xc4\xc294a\xc1Wd;A\xc0\xb0\x86>\x10S\xbd=\\\xfe\xfa=\xfeX8A\xfe\xa0\xf9\xbc\xe3j\x89=\xd6sB\xbc\xb7\xe7\xb5\xbf\xd5\xbe\xf7?\xa1\x9f~\xbf\xae\xc7\x9d\xbc\'n\x01Er\xf1\x11ER\x86\xccD\x07\xe2\xf4D\xf6\xae\xf1<X\x8cW=bo\xac\xb9\xb8s\x13\xb8\x00\x1a\x08<\x00\xd9\x1f<\x84/\x0f\xbd\xa4*\x0e\xbd\xa4\xfeG\xbd\xc4$c\xbd\x00\xe8F\xb8\x00&S9\xc0\x8cg;@\xd5J\xbb'
        expected_json = {'suspension-position': [12.61844253540039, 12.670042991638184, 46.231075286865234, 46.7338752746582], 'suspension-velocity': [-15.713324546813965, 16.78404426574707, -9.569318771362305, 12.916770935058594], 'suspension-acceleration': [-998.8273315429688, 982.3358764648438, -436.2744445800781, 823.2532348632812], 'wheel-speed': [11.483919143676758, 11.560998916625977, 11.475666999816895, 11.574358940124512], 'wheel-slip-ratio': [0.0008404557011090219, -0.0007693740190006793, 0.00011842480307677761, -8.53981327963993e-05], 'wheel-slip-angle': [0.0013498634798452258, -0.0037806208711117506, -0.002201445633545518, -0.002621696563437581], 'wheel-lat-force': [-303.59527587890625, 724.581787109375, 121.61688232421875, 448.942626953125], 'wheel-long-force': [97.64713287353516, -98.12667083740234, -14.075249671936035, 11.711997032165527], 'height-of-cog-above-ground': 0.26306724548339844, 'local-velocity': {'x': 0.09244358539581299, 'y': 0.12255546450614929, 'z': 11.521726608276367}, 'angular-velocity': {'x': -0.030472274869680405, 'y': 0.06709840148687363, 'z': -0.011868437752127647}, 'angular-acceleration': {'x': -1.4211338758468628, 'y': 1.9355112314224243, 'z': -0.9946232438087463}, 'front-wheels-angle': -0.019260253757238388, 'wheel-vert-force': [2070.884521484375, 2335.09033203125, 1636.197509765625, 1959.0633544921875], 'front-aero-height': 0.029502373188734055, 'rear-aero-height': 0.05262407660484314, 'front-roll-angle': -0.0003288938314653933, 'rear-roll-angle': -3.515530261211097e-05, 'chassis-yaw': 0.00830698013305664, 'chassis-pitch': 0.009756326675415039, 'wheel-camber': [-0.03495742380619049, -0.03470863401889801, -0.048826828598976135, -0.055454984307289124], 'wheel-camber-gain': [-4.7422945499420166e-05, 0.0002013668417930603, 0.0035331696271896362, -0.003094986081123352]}
        parsed_packet = PacketMotionExData(self.m_header_26, raw_packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))
