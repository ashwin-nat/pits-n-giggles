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
# pylint: skip-file

import os
from tempfile import NamedTemporaryFile
from colorama import Fore, Style
import sys
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.fuel_rate_recommender import FuelRemainingPerLap, FuelRateRecommender
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class FuelRecommenderUT(F1TelemetryUnitTestsBase):
    pass

class TestFuelRemainingPerLap(FuelRecommenderUT):
    def setUp(self):
        self.fuel_lap = FuelRemainingPerLap(
            lap_number=1,
            fuel_remaining=95.5,
            is_racing_lap=True,
            desc="Normal racing lap"
        )

    def test_initialization(self):
        self.assertEqual(self.fuel_lap.m_lap_number, 1)
        self.assertEqual(self.fuel_lap.m_fuel_remaining, 95.5)
        self.assertTrue(self.fuel_lap.m_is_racing_lap)
        self.assertEqual(self.fuel_lap.m_desc, "Normal racing lap")

    def test_default_values(self):
        basic_lap = FuelRemainingPerLap(
            lap_number=1,
            fuel_remaining=95.5
        )
        self.assertTrue(basic_lap.m_is_racing_lap)
        self.assertIsNone(basic_lap.m_desc)

    def test_json_conversion(self):
        json_data = self.fuel_lap.toJSON()
        self.assertEqual(json_data["lap-number"], 1)
        self.assertEqual(json_data["fuel-usage"], 95.5)
        self.assertTrue(json_data["is-racing-lap"])
        self.assertEqual(json_data["desc"], "Normal racing lap")

class TestFuelRateRecommender(FuelRecommenderUT):
    def setUp(self):
        # Initialize with starting conditions
        self.total_laps = 50
        self.min_fuel_kg = 1.0
        self.initial_history = [
            FuelRemainingPerLap(0, 100.0),  # Starting fuel
            FuelRemainingPerLap(1, 98.0)    # After first lap
        ]
        self.recommender = FuelRateRecommender(
            self.initial_history,
            self.total_laps,
            self.min_fuel_kg
        )

    def test_initialization(self):
        self.assertEqual(len(self.recommender.m_fuel_remaining_history), 2)
        self.assertEqual(self.recommender.m_total_laps, 50)
        self.assertEqual(self.recommender.m_min_fuel_kg, 1.0)

    def test_data_sufficiency(self):
        # Test with sufficient data
        self.assertTrue(self.recommender.isDataSufficient())

        # Test with insufficient data
        empty_recommender = FuelRateRecommender([], self.total_laps, self.min_fuel_kg)
        self.assertFalse(empty_recommender.isDataSufficient())

        single_lap_recommender = FuelRateRecommender(
            [FuelRemainingPerLap(0, 100.0)],
            self.total_laps,
            self.min_fuel_kg
        )
        self.assertFalse(single_lap_recommender.isDataSufficient())

    def test_clear(self):
        self.recommender.clear()
        self.assertEqual(len(self.recommender.m_fuel_remaining_history), 0)
        self.assertFalse(self.recommender.isDataSufficient())

    def test_fuel_used_last_lap(self):
        self.assertEqual(self.recommender.fuel_used_last_lap, 2.0)  # 100.0 - 98.0

        # Test with insufficient data
        empty_recommender = FuelRateRecommender([], self.total_laps, self.min_fuel_kg)
        self.assertIsNone(empty_recommender.fuel_used_last_lap)

    def test_current_fuel_rate(self):
        # Current fuel rate should be 2.0 kg/lap based on initial history
        self.assertEqual(self.recommender.curr_fuel_rate, 2.0)

    def test_target_fuel_rate(self):
        # Target fuel rate calculation:
        # (current_fuel - min_fuel) / laps_remaining
        # (98.0 - 1.0) / 49 ≈ 1.979592
        self.assertAlmostEqual(self.recommender.target_fuel_rate, 1.979592, places=6)

    def test_surplus_laps(self):
        # Surplus laps calculation:
        # (available_fuel / current_rate) - laps_remaining
        # ((98.0 - 1.0) / 2.0) - 49 ≈ -0.5
        self.assertAlmostEqual(self.recommender.surplus_laps, -0.5, places=6)

    def test_target_next_lap_fuel_usage(self):
        # Target next lap should be adjusted based on difference between current and target rate
        expected = self.recommender.target_fuel_rate - \
                  ((self.recommender.curr_fuel_rate - self.recommender.target_fuel_rate) * 0.5)
        self.assertAlmostEqual(self.recommender.target_next_lap_fuel_usage, expected, places=6)

    def test_add_fuel_reading(self):
        self.recommender.add(96.0, 2)  # Add third lap data
        self.assertEqual(len(self.recommender.m_fuel_remaining_history), 3)
        self.assertEqual(self.recommender.m_fuel_remaining_history[-1].m_fuel_remaining, 96.0)
        self.assertEqual(self.recommender.m_fuel_remaining_history[-1].m_lap_number, 2)

    def test_total_laps_property(self):
        # Test getter
        self.assertEqual(self.recommender.total_laps, 50)

        # Test setter
        self.recommender.total_laps = 55
        self.assertEqual(self.recommender.m_total_laps, 55)

    def test_edge_cases(self):
        # Test with last lap
        last_lap_history = [
            FuelRemainingPerLap(49, 3.0),
            FuelRemainingPerLap(50, 1.5)
        ]
        last_lap_recommender = FuelRateRecommender(last_lap_history, 50, self.min_fuel_kg)
        self.assertIsNone(last_lap_recommender.target_fuel_rate)
        self.assertIsNone(last_lap_recommender.target_next_lap_fuel_usage)
        self.assertIsNone(last_lap_recommender.surplus_laps)

        # Test with zero current fuel rate
        zero_rate_history = [
            FuelRemainingPerLap(0, 100.0),
            FuelRemainingPerLap(1, 100.0)
        ]
        zero_rate_recommender = FuelRateRecommender(zero_rate_history, 50, self.min_fuel_kg)
        self.assertIsNone(zero_rate_recommender.surplus_laps)
