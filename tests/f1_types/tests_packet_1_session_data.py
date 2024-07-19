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
from lib.f1_types import PacketSessionData, F1PacketType
from .tests_parser_base import F1TypesTest

class TestPacketSessionData(F1TypesTest):
    """
    Tests for PacketSessionData
    """
    def setUp(self) -> None:
        """
        Set up the test
        """
        self.m_num_players = random.randint(1, 22)

    def test_f1_23(self):
        """
        Test for F1 2023
        """

        # This packet is way too huge to write from_values and to_bytes
        # Hence, we are comparing
        packet = (
                b'\x01\x1e\x16\x19\xe3\x10\n\x11\x00\xe2\x1b \x1cP\x00\x00\xff\x00\rO\xa7}?\x03\x8a-\xa2=\x03E\xf1'
                b'\x02>\x03\xef\xfe]>\x03\xc5?\x97>\x03\x12P\xb0>\x03&\xa5\xd7>\x03>\xd3\n?\x03^\x99\x17?\x03H\xf4+?'
                b'\x03\xd3a??\x03\x07\xfeL?\x03\xf5)h?\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x02\x01\x05\n\x00\x01\x1f\x02\x16\x02\x0c\n\x05\x01\x1f\x02\x16\x02\x0f\n\n\x02\x1e\x01\x16\x02'
                b'\x11\n\x0f\x02\x1d\x01\x16\x02\x1c\n\x1e\x03\x1b\x01\x16\x02K\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01_\xfeS\xfag\xfeS\xfag\xfeS\xfag'
                b'\x0c\x17\x14\x00\x00\x01\x00\x00\x00\x00\x02\x01\x07\x01\xd4\x02\x00\x00' \
                b'\x05\x01\x00\x01\x00\x00\x01\x00'
        )

        expected_json = {
            "weather": "Light Cloud",
            "track-temperature": 30,
            "air-temperature": 22,
            "total-laps": 25,
            "track-length": 4323,
            "session-type": "Race",
            "track-id": "Austria",
            "formula": "F1 Modern",
            "session-time-left": 7138,
            "session-duration": 7200,
            "pit-speed-limit": 80,
            "game-paused": 0,
            "is-spectating": 0,
            "spectator-car-index": 255,
            "sli-pro-native-support": 0,
            "num-marshal-zones": 13,
            "marshal-zones": [
                {
                    "zone-start": 0.9908341765403748,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.07918842136859894,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.127873495221138,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.21679280698299408,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.2954083979129791,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.344360888004303,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.421181857585907,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.5422857999801636,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.5921839475631714,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.6716961860656738,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.7475864291191101,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.8007511496543884,
                    "zone-flag": "YELLOW_FLAG"
                },
                {
                    "zone-start": 0.9068902134895325,
                    "zone-flag": "YELLOW_FLAG"
                }
            ],
            "safety-car-status": "VIRTUAL_SAFETY_CAR",
            "network-game": 1,
            "num-weather-forecast-samples": 5,
            "weather-forecast-samples": [
                {
                    "session-type": "Race",
                    "time-offset": 0,
                    "weather": "Light Cloud",
                    "track-temperature": 31,
                    "track-temperature-change": "No Temperature Change",
                    "air-temperature": 22,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 12
                },
                {
                    "session-type": "Race",
                    "time-offset": 5,
                    "weather": "Light Cloud",
                    "track-temperature": 31,
                    "track-temperature-change": "No Temperature Change",
                    "air-temperature": 22,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 15
                },
                {
                    "session-type": "Race",
                    "time-offset": 10,
                    "weather": "Overcast",
                    "track-temperature": 30,
                    "track-temperature-change": "Temperature Down",
                    "air-temperature": 22,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 17
                },
                {
                    "session-type": "Race",
                    "time-offset": 15,
                    "weather": "Overcast",
                    "track-temperature": 29,
                    "track-temperature-change": "Temperature Down",
                    "air-temperature": 22,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 28
                },
                {
                    "session-type": "Race",
                    "time-offset": 30,
                    "weather": "Light Rain",
                    "track-temperature": 27,
                    "track-temperature-change": "Temperature Down",
                    "air-temperature": 22,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 75
                }
            ],
            "forecast-accuracy": 1,
            "ai-difficulty": 95,
            "season-link-identifier": 1744458750,
            "weekend-link-identifier": 1744458750,
            "session-link-identifier": 1744458750,
            "pit-stop-window-ideal-lap": 12,
            "pit-stop-window-latest-lap": 23,
            "pit-stop-rejoin-position": 20,
            "steering-assist": 0,
            "braking-assist": 0,
            "gearbox-assist": "Manaul",
            "pit-assist": 0,
            "pit-release-assist": 0,
            "ers-assist": 0,
            "drs-assist": 0,
            "dynamic-racing-line": 2,
            "dynamic-racing-line-type": 1,
            "game-mode": "Online Custom",
            "rule-set": "Race",
            "time-of-day": 724,
            "session-length": "Medium Long",
            "speed-units-lead-player": 1,
            "temp-units-lead-player": 0,
            "speed-units-secondary-player": 1,
            "temp-units-secondary-player": 0,
            "num-safety-car-periods": 0,
            "num-virtual-safety-car-periods": 1,
            "num-red-flag-periods": 0,
            "equal-car-performance": "0",
            "recovery-mode": "0",
            "flashback-limit": "0",
            "surface-type": "0",
            "low-fuel-mode": "0",
            "race-starts": "0",
            "tyre-temperature-mode": "0",
            "pit-lane-tyre-sim": "0",
            "car-damage": "0",
            "car-damage-rate": "0",
            "collisions": "0",
            "collisions-off-for-first-lap-only": 0,
            "mp-unsafe-pit-release": 0,
            "mp-off-for-griefing": 0,
            "corner-cutting-stringency": "0",
            "parc-ferme-rules": 0,
            "pit-stop-experience": 0,
            "safety-car-setting": "0",
            "safety-car-experience": "0",
            "formation-lap": 0,
            "formation-lap-experience": "0",
            "red-flags-setting": "0",
            "affects-license-level-solo": 0,
            "affects-license-level-mp": 0,
            "num-sessions-in-weekend": "0",
            "weekend-structure": [
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0"
            ],
            "sector-2-lap-distance-start": "0.0",
            "sector-3-lap-distance-start": "0.0"
        }

        random_header = F1TypesTest.getRandomHeader(F1PacketType.SESSION, 23, self.m_num_players)
        parsed_packet = PacketSessionData(random_header, packet)
        parsed_json = parsed_packet.toJSON()
        self.assertEqual(expected_json, parsed_json)

    def test_f1_24(self):
        """
        Test parsing F1 2024 SessionData packet
        """

        # This packet is way too huge to write from_values and to_bytes
        # Hence, we are comparing
        packet = (
            b'\x01\x1b\x13\x05_\x1b\x0f\n\x00 \x1c \x1cP\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x03\x0f\x00\x01\x1b\x02\x13'
            b'\x02\x0e\x0f\x05\x01\x1b\x02\x13\x02\x0e\x0f\n\x01\x1b\x02\x13\x02\x0e\x00\x00\x00\x00\x00\x00\x00\x00'
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
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1d\xb1\x8c/\x81\xb1\x8c/\x81\xb1\x8c/\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x01\xd6\x02\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00$<\x11E\x12H\x9eE'
        )

        expected_json = {
            "weather": "Light Cloud",
            "track-temperature": 27,
            "air-temperature": 19,
            "total-laps": 5,
            "track-length": 7007,
            "session-type": "Race",
            "track-id": "Spa",
            "formula": "F1 Modern",
            "session-time-left": 7200,
            "session-duration": 7200,
            "pit-speed-limit": 80,
            "game-paused": 0,
            "is-spectating": 0,
            "spectator-car-index": 0,
            "sli-pro-native-support": 0,
            "num-marshal-zones": 0,
            "marshal-zones": [],
            "safety-car-status": "NO_SAFETY_CAR",
            "network-game": 1,
            "num-weather-forecast-samples": 3,
            "weather-forecast-samples": [
                {
                    "session-type": "Race",
                    "time-offset": 0,
                    "weather": "Light Cloud",
                    "track-temperature": 27,
                    "track-temperature-change": "No Temperature Change",
                    "air-temperature": 19,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 14
                },
                {
                    "session-type": "Race",
                    "time-offset": 5,
                    "weather": "Light Cloud",
                    "track-temperature": 27,
                    "track-temperature-change": "No Temperature Change",
                    "air-temperature": 19,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 14
                },
                {
                    "session-type": "Race",
                    "time-offset": 10,
                    "weather": "Light Cloud",
                    "track-temperature": 27,
                    "track-temperature-change": "No Temperature Change",
                    "air-temperature": 19,
                    "air-temperature-change": "No Temperature Change",
                    "rain-percentage": 14
                }
            ],
            "forecast-accuracy": 0,
            "ai-difficulty": 0,
            "season-link-identifier": 797749533,
            "weekend-link-identifier": 797749633,
            "session-link-identifier": 797749633,
            "pit-stop-window-ideal-lap": 0,
            "pit-stop-window-latest-lap": 0,
            "pit-stop-rejoin-position": 0,
            "steering-assist": 0,
            "braking-assist": 0,
            "gearbox-assist": "0",
            "pit-assist": 0,
            "pit-release-assist": 0,
            "ers-assist": 0,
            "drs-assist": 0,
            "dynamic-racing-line": 0,
            "dynamic-racing-line-type": 0,
            "game-mode": "Online Custom",
            "rule-set": "Race",
            "time-of-day": 726,
            "session-length": "Short",
            "speed-units-lead-player": 0,
            "temp-units-lead-player": 0,
            "speed-units-secondary-player": 0,
            "temp-units-secondary-player": 0,
            "num-safety-car-periods": 0,
            "num-virtual-safety-car-periods": 0,
            "num-red-flag-periods": 0,
            "equal-car-performance": "0",
            "recovery-mode": "0",
            "flashback-limit": "0",
            "surface-type": "0",
            "low-fuel-mode": "0",
            "race-starts": "0",
            "tyre-temperature-mode": "0",
            "pit-lane-tyre-sim": "0",
            "car-damage": "0",
            "car-damage-rate": "0",
            "collisions": "0",
            "collisions-off-for-first-lap-only": 0,
            "mp-unsafe-pit-release": 0,
            "mp-off-for-griefing": 0,
            "corner-cutting-stringency": "0",
            "parc-ferme-rules": 0,
            "pit-stop-experience": 0,
            "safety-car-setting": "0",
            "safety-car-experience": "0",
            "formation-lap": 0,
            "formation-lap-experience": "0",
            "red-flags-setting": "0",
            "affects-license-level-solo": 0,
            "affects-license-level-mp": 0,
            "num-sessions-in-weekend": "0",
            "weekend-structure": [],
            "sector-2-lap-distance-start": "2323.7587890625",
            "sector-3-lap-distance-start": "5065.0087890625"
        }

        random_header = F1TypesTest.getRandomHeader(F1PacketType.MOTION, 24, self.m_num_players)
        parsed_packet = PacketSessionData(random_header, packet)
        parsed_json = parsed_packet.toJSON()
        self.assertEqual(expected_json, parsed_json)
