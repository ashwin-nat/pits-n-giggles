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

from typing import List

from tests_base import F1TelemetryUnitTestsBase

from lib.tyre_wear_extrapolator import TyreWearExtrapolator, TyreWearPerLap


class TestTyreWear(F1TelemetryUnitTestsBase):

    def setUp(self):
        self.sample_data: List[TyreWearPerLap] = [
            TyreWearPerLap(80, 81, 78, 79, lap_number=1),
            TyreWearPerLap(77, 76, 75, 74, lap_number=2),
            TyreWearPerLap(72, 73, 70, 71, lap_number=3),
            TyreWearPerLap(68, 69, 66, 67, lap_number=4),
        ]
        self.total_laps = 10
        self.extrapolator = TyreWearExtrapolator(self.sample_data, self.total_laps)

    def test_average_computation(self):
        lap = TyreWearPerLap(80, 80, 80, 80)
        self.assertAlmostEqual(lap.m_average, 80.0)

    def test_toJSON_structure(self):
        lap = TyreWearPerLap(90, 85, 80, 75, lap_number=5, desc="Test Lap")
        json_data = lap.toJSON()
        self.assertEqual(json_data["lap-number"], 5)
        self.assertEqual(json_data["desc"], "Test Lap")
        self.assertIn("average", json_data)

    def test_get_prediction_latest_lap(self):
        pred = self.extrapolator.getTyreWearPrediction()
        self.assertIsInstance(pred, TyreWearPerLap)

    def test_get_prediction_specific_lap(self):
        pred = self.extrapolator.getTyreWearPrediction(lap_number=10)
        self.assertIsInstance(pred, TyreWearPerLap)
        self.assertEqual(pred.lap_number, 10)

    def test_remaining_laps_calculation(self):
        self.assertEqual(self.extrapolator.remaining_laps, 6)  # last lap was 4, total is 10

    def test_data_sufficiency(self):
        self.assertTrue(self.extrapolator.isDataSufficient())

    def test_clear_data(self):
        self.extrapolator.clear()
        self.assertFalse(self.extrapolator.isDataSufficient())

    def test_add_lap(self):
        new_lap = TyreWearPerLap(65, 64, 63, 62, lap_number=5)
        self.extrapolator.add(new_lap)
        self.assertEqual(self.extrapolator.m_initial_data[-1].lap_number, 5)

    def test_remove_lap(self):
        self.extrapolator.remove([2])  # Should remove lap 2
        laps_left = [lap.lap_number for lap in self.extrapolator.m_initial_data]
        self.assertNotIn(2, laps_left)

    def test_num_samples(self):
        self.assertEqual(self.extrapolator.num_samples, len(self.sample_data))