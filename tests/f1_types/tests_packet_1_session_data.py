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
            "is-spectating": False,
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
            "gearbox-assist": "Manual",
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
            "recovery-mode": "NONE",
            "flashback-limit": "LOW",
            "surface-type": "SIMPLIFIED",
            "low-fuel-mode": "EASY",
            "race-starts": "MANUAL",
            "tyre-temperature-mode": "SURFACE_ONLY",
            "pit-lane-tyre-sim": "0",
            "car-damage": "OFF",
            "car-damage-rate": "REDUCED",
            "collisions": "OFF",
            "collisions-off-for-first-lap-only": 0,
            "mp-unsafe-pit-release": 0,
            "mp-off-for-griefing": 0,
            "corner-cutting-stringency": "REGULAR",
            "parc-ferme-rules": 0,
            "pit-stop-experience": "AUTOMATIC",
            "safety-car-setting": "OFF",
            "safety-car-experience": "BROADCAST",
            "formation-lap": 0,
            "formation-lap-experience": "BROADCAST",
            "red-flags-setting": "OFF",
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
            "sector-3-lap-distance-start": "0.0",
            "active-aero-track-status": "0",
            "num-active-aero-zones-full": 0,
            "active-aero-zones-full": [],
            "num-active-aero-zones-partial": 0,
            "active-aero-zones-partial": [],
            "num-drs-zones": 0,
            "drs-zones": [],
            "start-reaction-time": 0.0,
            "anti-lock-brakes-assist": 0,
            "traction-control-assist": "0",
            "dynamic-racing-line-hi-vis": 0,
            "dynamic-racing-line-colour-blind": "0",
            "recurring-rewind-prompt": 0,
        }

        random_header = F1TypesTest.getRandomHeader(F1PacketType.SESSION, 23, self.m_num_players)
        parsed_packet = PacketSessionData(random_header, packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))
        self.assertEqual(parsed_packet, PacketSessionData(random_header, packet))

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
            "is-spectating": False,
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
            "gearbox-assist": "Unknown",
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
            "recovery-mode": "NONE",
            "flashback-limit": "LOW",
            "surface-type": "SIMPLIFIED",
            "low-fuel-mode": "EASY",
            "race-starts": "MANUAL",
            "tyre-temperature-mode": "SURFACE_ONLY",
            "pit-lane-tyre-sim": "0",
            "car-damage": "OFF",
            "car-damage-rate": "REDUCED",
            "collisions": "OFF",
            "collisions-off-for-first-lap-only": 0,
            "mp-unsafe-pit-release": 0,
            "mp-off-for-griefing": 0,
            "corner-cutting-stringency": "REGULAR",
            "parc-ferme-rules": 0,
            "pit-stop-experience": "AUTOMATIC",
            "safety-car-setting": "OFF",
            "safety-car-experience": "BROADCAST",
            "formation-lap": 0,
            "formation-lap-experience": "BROADCAST",
            "red-flags-setting": "OFF",
            "affects-license-level-solo": 0,
            "affects-license-level-mp": 0,
            "num-sessions-in-weekend": "0",
            "weekend-structure": [],
            "sector-2-lap-distance-start": "2323.7587890625",
            "sector-3-lap-distance-start": "5065.0087890625",
            "active-aero-track-status": "0",
            "num-active-aero-zones-full": 0,
            "active-aero-zones-full": [],
            "num-active-aero-zones-partial": 0,
            "active-aero-zones-partial": [],
            "num-drs-zones": 0,
            "drs-zones": [],
            "start-reaction-time": 0.0,
            "anti-lock-brakes-assist": 0,
            "traction-control-assist": "0",
            "dynamic-racing-line-hi-vis": 0,
            "dynamic-racing-line-colour-blind": "0",
            "recurring-rewind-prompt": 0,
        }

        random_header = F1TypesTest.getRandomHeader(F1PacketType.SESSION, 24, self.m_num_players)
        parsed_packet = PacketSessionData(random_header, packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))

    def test_f1_25(self):

        packet = b'\x00\x00\x00\x05\xe3\x10\x0f(\x00 \x1c \x1cP\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc8=\xccC\xc8=\xccC\xc8=\xccC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xad\x91\xadDb\xf8BE'
        expected_json = {"weather": "Clear", "track-temperature": 0, "air-temperature": 0, "total-laps": 5, "track-length": 4323, "session-type": "Race", "track-id": "Austria_Reverse", "formula": "F1 Modern", "session-time-left": 7200, "session-duration": 7200, "pit-speed-limit": 80, "game-paused": 0, "is-spectating": False, "spectator-car-index": 0, "sli-pro-native-support": 0, "num-marshal-zones": 0, "marshal-zones": [], "safety-car-status": "NO_SAFETY_CAR", "network-game": 0, "num-weather-forecast-samples": 0, "weather-forecast-samples": [], "forecast-accuracy": 0, "ai-difficulty": 0, "season-link-identifier": 1137458632, "weekend-link-identifier": 1137458632, "session-link-identifier": 1137458632, "pit-stop-window-ideal-lap": 0, "pit-stop-window-latest-lap": 0, "pit-stop-rejoin-position": 0, "steering-assist": 0, "braking-assist": 0, "gearbox-assist": "Unknown", "pit-assist": 0, "pit-release-assist": 0, "ers-assist": 0, "drs-assist": 0, "dynamic-racing-line": 0, "dynamic-racing-line-type": 0, "game-mode": "Event Mode", "rule-set": "Race", "time-of-day": 0, "session-length": "Short", "speed-units-lead-player": 0, "temp-units-lead-player": 0, "speed-units-secondary-player": 0, "temp-units-secondary-player": 0, "num-safety-car-periods": 0, "num-virtual-safety-car-periods": 0, "num-red-flag-periods": 0, "equal-car-performance": "0", "recovery-mode": "NONE", "flashback-limit": "LOW", "surface-type": "SIMPLIFIED", "low-fuel-mode": "EASY", "race-starts": "MANUAL", "tyre-temperature-mode": "SURFACE_ONLY", "pit-lane-tyre-sim": "0", "car-damage": "OFF", "car-damage-rate": "REDUCED", "collisions": "OFF", "collisions-off-for-first-lap-only": 0, "mp-unsafe-pit-release": 0, "mp-off-for-griefing": 0, "corner-cutting-stringency": "REGULAR", "parc-ferme-rules": 0, "pit-stop-experience": "AUTOMATIC", "safety-car-setting": "OFF", "safety-car-experience": "BROADCAST", "formation-lap": 0, "formation-lap-experience": "BROADCAST", "red-flags-setting": "OFF", "affects-license-level-solo": 0, "affects-license-level-mp": 0, "num-sessions-in-weekend": "0", "weekend-structure": [], "sector-2-lap-distance-start": "1388.5523681640625", "sector-3-lap-distance-start": "3119.52392578125", "active-aero-track-status": "0", "num-active-aero-zones-full": 0, "active-aero-zones-full": [], "num-active-aero-zones-partial": 0, "active-aero-zones-partial": [], "num-drs-zones": 0, "drs-zones": [], "start-reaction-time": 0.0, "anti-lock-brakes-assist": 0, "traction-control-assist": "0", "dynamic-racing-line-hi-vis": 0, "dynamic-racing-line-colour-blind": "0", "recurring-rewind-prompt": 0}

        random_header = F1TypesTest.getRandomHeader(F1PacketType.SESSION, 25, self.m_num_players)
        parsed_packet = PacketSessionData(random_header, packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))
        self.assertEqual(parsed_packet, PacketSessionData(random_header, packet))

    def test_f1_26_actual(self):

        packet = b'\x02!\x17\x03\x02\x17\x01\x07\r\xc7\x0b\x10\x0e<\x00\x00\xff\x00\x0e\x98>0=\x00\xc5\xbe\x0b>\x00\xa3\xf92>\x00b\x11R>\x00\xc9\xc7\x88>\x00\xbc\xd9\x9e>\x00\xb3\x15\xbc>\x00\x8c\xee\xe0>\x00a\x1e\x00?\x00l\xa1\x18?\x00!O>?\x00guR?\x00\xcc\xc1h?\x00\xe7Ev?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00-\x01\x00\x02!\x02\x17\x02\x11\x01\x05\x02!\x02\x17\x02\x11\x01\n\x02!\x02\x17\x02\x11\x01\x0f\x02!\x02\x17\x02\x11\x01\x1e\x02!\x02\x17\x02\x10\x01-\x02!\x02\x17\x02\x10\x01<\x02!\x02\x17\x02\x10\x02\x00\x02"\x00\x18\x00\x11\x02\x05\x02"\x02\x18\x02\x13\x02\n\x02"\x02\x18\x02\x14\x02\x0f\x02"\x02\x17\x01\x15\x02\x1e\x02!\x01\x17\x02\x18\x02-\x02 \x01\x17\x02\x18\x02<\x02\x1f\x01\x16\x01\x18\x03\x00\x02%\x00\x19\x00\x11\x03\x05\x02%\x02\x19\x02\x13\x03\n\x02%\x02\x19\x02\x14\x03\x0f\x02%\x02\x19\x02\x15\x03\x1e\x02%\x02\x19\x02\x18\x03-\x02%\x02\x19\x02\x18\x03<\x02%\x02\x19\x02\x18\x05\x00\x02 \x01\x17\x02\x11\x05\x05\x02 \x02\x17\x02\x11\x05\n\x02 \x02\x17\x02\x11\x05\x0f\x02 \x02\x17\x02\x12\x05\x14\x02 \x02\x17\x02\x12\x06\x00\x02 \x01\x17\x02\x11\x06\x05\x02 \x02\x17\x02\x11\x06\n\x02 \x02\x17\x02\x11\x06\x0f\x02 \x02\x17\x02\x12\x06\x14\x02 \x02\x17\x02\x12\x07\x00\x02 \x01\x17\x02\x11\x07\x05\x02 \x02\x17\x02\x11\x07\n\x02 \x02\x17\x02\x11\x07\x0f\x02 \x02\x17\x02\x12\x07\x14\x02 \x02\x17\x02\x12\x0f\x00\x02$\x00\x19\x00\x17\x0f\x05\x02$\x02\x19\x02\x17\x0f\n\x02$\x02\x19\x02\x17\x0f\x0f\x02$\x02\x19\x02\x16\x0f\x1e\x02$\x02\x19\x02\x16\x0f-\x02$\x02\x19\x02\x15\x0f<\x02$\x02\x19\x02\x15\x0fZ\x02#\x01\x18\x01\x13\x0fx\x02"\x01\x17\x01\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00^H\xd3\x14\xd8H\xd3\x14\xd8H\xd3\x14\xd8\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04\x00\xf7\x02\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x01\x01\x01\x01\x01\x00\x01\x00\x01\x01\x02\x00\x00\x00\x00\x01\x02\x03\x01\x00\xff\x02\x00\x01\x07\x01\x02\x03\x05\x06\x07\x0f\x00\x00\x00\x00\x00\x1f\x9b\xe2D\xa6+\x86E\x00\x04O\xbe~?\xfa\xc7-=\xf4\xe9d>\xbej\xa1>Eg\xcc>u(\xfd>\x12\x0c9?\xdaSX?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03$8e;\xfa\xc7-=\x17_o>\xbej\xa1>\xa8\xa9;?\xdaSX?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xf4\xe9d>\n\xba\xa3>s\xa26?_\xaaU?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_json = {'weather': 'Overcast', 'track-temperature': 33, 'air-temperature': 23, 'total-laps': 3, 'track-length': 5890, 'session-type': 'Practice 1', 'track-id': 'Silverstone', 'formula': 'F1 26', 'session-time-left': 3015, 'session-duration': 3600, 'pit-speed-limit': 60, 'game-paused': 0, 'is-spectating': False, 'spectator-car-index': 255, 'sli-pro-native-support': 0, 'num-marshal-zones': 14, 'marshal-zones': [{'zone-start': 0.043028444051742554, 'zone-flag': 'NONE'}, {'zone-start': 0.13646991550922394, 'zone-flag': 'NONE'}, {'zone-start': 0.17478041350841522, 'zone-flag': 'NONE'}, {'zone-start': 0.20514443516731262, 'zone-flag': 'NONE'}, {'zone-start': 0.2671492397785187, 'zone-flag': 'NONE'}, {'zone-start': 0.31025493144989014, 'zone-flag': 'NONE'}, {'zone-start': 0.36735305190086365, 'zone-flag': 'NONE'}, {'zone-start': 0.4393199682235718, 'zone-flag': 'NONE'}, {'zone-start': 0.5004635453224182, 'zone-flag': 'NONE'}, {'zone-start': 0.5962131023406982, 'zone-flag': 'NONE'}, {'zone-start': 0.7433949112892151, 'zone-flag': 'NONE'}, {'zone-start': 0.8221039175987244, 'zone-flag': 'NONE'}, {'zone-start': 0.9092071056365967, 'zone-flag': 'NONE'}, {'zone-start': 0.9620041251182556, 'zone-flag': 'NONE'}], 'safety-car-status': 'NO_SAFETY_CAR', 'network-game': 0, 'num-weather-forecast-samples': 45, 'weather-forecast-samples': [{'session-type': 'Practice 1', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Practice 1', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Practice 1', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Practice 1', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Practice 1', 'time-offset': 30, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 16}, {'session-type': 'Practice 1', 'time-offset': 45, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 16}, {'session-type': 'Practice 1', 'time-offset': 60, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 16}, {'session-type': 'Practice 2', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 34, 'track-temperature-change': 'Temperature Up', 'air-temperature': 24, 'air-temperature-change': 'Temperature Up', 'rain-percentage': 17}, {'session-type': 'Practice 2', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 34, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 24, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 19}, {'session-type': 'Practice 2', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 34, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 24, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 20}, {'session-type': 'Practice 2', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 34, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'Temperature Down', 'rain-percentage': 21}, {'session-type': 'Practice 2', 'time-offset': 30, 'weather': 'Overcast', 'track-temperature': 33, 'track-temperature-change': 'Temperature Down', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 24}, {'session-type': 'Practice 2', 'time-offset': 45, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'Temperature Down', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 24}, {'session-type': 'Practice 2', 'time-offset': 60, 'weather': 'Overcast', 'track-temperature': 31, 'track-temperature-change': 'Temperature Down', 'air-temperature': 22, 'air-temperature-change': 'Temperature Down', 'rain-percentage': 24}, {'session-type': 'Practice 3', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'Temperature Up', 'air-temperature': 25, 'air-temperature-change': 'Temperature Up', 'rain-percentage': 17}, {'session-type': 'Practice 3', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 19}, {'session-type': 'Practice 3', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 20}, {'session-type': 'Practice 3', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 21}, {'session-type': 'Practice 3', 'time-offset': 30, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 24}, {'session-type': 'Practice 3', 'time-offset': 45, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 24}, {'session-type': 'Practice 3', 'time-offset': 60, 'weather': 'Overcast', 'track-temperature': 37, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 24}, {'session-type': 'Qualifying 1', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'Temperature Down', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 1', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 1', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 1', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 18}, {'session-type': 'Qualifying 1', 'time-offset': 20, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 18}, {'session-type': 'Qualifying 2', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'Temperature Down', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 2', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 2', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 2', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 18}, {'session-type': 'Qualifying 2', 'time-offset': 20, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 18}, {'session-type': 'Qualifying 3', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'Temperature Down', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 3', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 3', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 17}, {'session-type': 'Qualifying 3', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 18}, {'session-type': 'Qualifying 3', 'time-offset': 20, 'weather': 'Overcast', 'track-temperature': 32, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 23, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 18}, {'session-type': 'Race', 'time-offset': 0, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'Temperature Up', 'air-temperature': 25, 'air-temperature-change': 'Temperature Up', 'rain-percentage': 23}, {'session-type': 'Race', 'time-offset': 5, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 23}, {'session-type': 'Race', 'time-offset': 10, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 23}, {'session-type': 'Race', 'time-offset': 15, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 22}, {'session-type': 'Race', 'time-offset': 30, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 22}, {'session-type': 'Race', 'time-offset': 45, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 21}, {'session-type': 'Race', 'time-offset': 60, 'weather': 'Overcast', 'track-temperature': 36, 'track-temperature-change': 'No Temperature Change', 'air-temperature': 25, 'air-temperature-change': 'No Temperature Change', 'rain-percentage': 21}, {'session-type': 'Race', 'time-offset': 90, 'weather': 'Overcast', 'track-temperature': 35, 'track-temperature-change': 'Temperature Down', 'air-temperature': 24, 'air-temperature-change': 'Temperature Down', 'rain-percentage': 19}, {'session-type': 'Race', 'time-offset': 120, 'weather': 'Overcast', 'track-temperature': 34, 'track-temperature-change': 'Temperature Down', 'air-temperature': 23, 'air-temperature-change': 'Temperature Down', 'rain-percentage': 19}], 'forecast-accuracy': 0, 'ai-difficulty': 94, 'season-link-identifier': 3625243464, 'weekend-link-identifier': 3625243464, 'session-link-identifier': 3625243464, 'pit-stop-window-ideal-lap': 0, 'pit-stop-window-latest-lap': 0, 'pit-stop-rejoin-position': 0, 'steering-assist': 0, 'braking-assist': 0, 'gearbox-assist': 'Manual', 'pit-assist': 0, 'pit-release-assist': 0, 'ers-assist': 0, 'drs-assist': 0, 'dynamic-racing-line': 0, 'dynamic-racing-line-type': 0, 'game-mode': 'Grand Prix 23', 'rule-set': 'Practice & Qualifying', 'time-of-day': 759, 'session-length': 'None', 'speed-units-lead-player': 1, 'temp-units-lead-player': 0, 'speed-units-secondary-player': 1, 'temp-units-secondary-player': 0, 'num-safety-car-periods': 0, 'num-virtual-safety-car-periods': 0, 'num-red-flag-periods': 0, 'equal-car-performance': '1', 'recovery-mode': 'FLASHBACKS', 'flashback-limit': 'MEDIUM', 'surface-type': 'REALISTIC', 'low-fuel-mode': 'HARD', 'race-starts': 'MANUAL', 'tyre-temperature-mode': 'SURFACE_AND_CARCASS', 'pit-lane-tyre-sim': '0', 'car-damage': 'REDUCED', 'car-damage-rate': 'STANDARD', 'collisions': 'ON', 'collisions-off-for-first-lap-only': 0, 'mp-unsafe-pit-release': 0, 'mp-off-for-griefing': 0, 'corner-cutting-stringency': 'REGULAR', 'parc-ferme-rules': 1, 'pit-stop-experience': 'IMMERSIVE', 'safety-car-setting': 'INCREASED', 'safety-car-experience': 'IMMERSIVE', 'formation-lap': 0, 'formation-lap-experience': '255', 'red-flags-setting': 'STANDARD', 'affects-license-level-solo': 0, 'affects-license-level-mp': 1, 'num-sessions-in-weekend': '7', 'weekend-structure': ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying 1', 'Qualifying 2', 'Qualifying 3', 'Race'], 'sector-2-lap-distance-start': '1812.8475341796875', 'sector-3-lap-distance-start': '4293.4560546875', 'active-aero-track-status': 'FULL', 'num-active-aero-zones-full': 4, 'active-aero-zones-full': [{'zone-start': 0.9950913786888123, 'zone-end': 0.04242704063653946}, {'zone-start': 0.22354871034622192, 'zone-end': 0.31526750326156616}, {'zone-start': 0.3992253839969635, 'zone-end': 0.49444928765296936}, {'zone-start': 0.722840428352356, 'zone-end': 0.8450294733047485}], 'num-active-aero-zones-partial': 3, 'active-aero-zones-partial': [{'zone-start': 0.0034976089373230934, 'zone-end': 0.04242704063653946}, {'zone-start': 0.23376117646694183, 'zone-end': 0.31526750326156616}, {'zone-start': 0.7330574989318848, 'zone-end': 0.8450294733047485}], 'num-drs-zones': 2, 'drs-zones': [{'zone-start': 0.22354871034622192, 'zone-end': 0.3197787404060364}, {'zone-start': 0.7134162783622742, 'zone-end': 0.8346309065818787}], 'start-reaction-time': 0.0, 'anti-lock-brakes-assist': False, 'traction-control-assist': 'OFF', 'dynamic-racing-line-hi-vis': 0, 'dynamic-racing-line-colour-blind': 'OFF', 'recurring-rewind-prompt': 0}

        random_header = F1TypesTest.getRandomHeader(F1PacketType.SESSION, 26, self.m_num_players)
        parsed_packet = PacketSessionData(random_header, packet)
        parsed_json = parsed_packet.toJSON()
        self.jsonComparisionUtil(expected_json, parsed_json)
        self.assertFalse(hasattr(parsed_packet, '__dict__'))
        self.assertEqual(parsed_packet, PacketSessionData(random_header, packet))
