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
from lib.tyre_wear_extrapolator.simple_linear_regression import SimpleLinearRegression


class TestTyreWearPrediction(F1TelemetryUnitTestsBase):
    pass

class TestSimpleLinearRegression(TestTyreWearPrediction):

    def test_fit_with_multiple_points(self):
        model = SimpleLinearRegression()
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        model.fit(x, y)

        # Check if the model's slope (m) and intercept (c) match the expected values
        self.assertEqual(model.slope, 2.0)
        self.assertEqual(model.c, 0.0)

    def test_fit_with_single_point(self):
        model = SimpleLinearRegression()
        x = [2]
        y = [5]
        model.fit(x, y)

        # With only one point, slope is assumed to be 0, and the intercept is the y value
        self.assertEqual(model.slope, 0)
        self.assertEqual(model.c, 5)

    def test_fit_with_empty_lists(self):
        model = SimpleLinearRegression()
        with self.assertRaises(ValueError):
            model.fit([], [])

    def test_predict(self):
        model = SimpleLinearRegression()
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        model.fit(x, y)

        # Predict the value for x = 6, should return 12 as per the model
        self.assertEqual(model.predict(6), 12.0)

    def test_predict_with_invalid_type(self):
        model = SimpleLinearRegression()
        with self.assertRaises(ValueError):
            model.predict('string')  # Passing a non-integer type

    def test_fit_with_discontinuous_laps(self):
        model = SimpleLinearRegression()
        x = [1, 3, 4, 6]  # Skipped laps
        y = [90, 80, 75, 65]
        model.fit(x, y)
        self.assertTrue(0 <= model.r2 <= 1)

    def test_fit_with_poor_fit(self):
        model = SimpleLinearRegression()
        x = [1, 2, 3, 4, 5]
        y = [10, 9, 11, 10, 9]  # Noisy, weak correlation
        model.fit(x, y)
        self.assertLess(model.r2, 0.5)

    def test_fit_with_perfect_fit(self):
        model = SimpleLinearRegression()
        x = [1, 2, 3, 4, 5]
        y = [5, 10, 15, 20, 25]
        model.fit(x, y)
        self.assertAlmostEqual(model.r2, 1.0)

class TestTyreWearExtrapolator(TestTyreWearPrediction):

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

    def test_empty_initial_data(self):
        # Create extrapolator with empty data
        extrapolator = TyreWearExtrapolator(initial_data=[], total_laps=None)
        # isDataSufficient should be False
        self.assertFalse(extrapolator.isDataSufficient())
        # num_samples should be 0
        self.assertEqual(extrapolator.num_samples, 0)

class TestTyreWearExtrapolatorWithNonRacingLaps(TestTyreWearPrediction):
    def setUp(self):
        self.mixed_data: List[TyreWearPerLap] = [
            TyreWearPerLap(80, 81, 78, 79, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(79, 79, 78, 78, lap_number=2, is_racing_lap=False),  # SC lap
            TyreWearPerLap(77, 76, 75, 74, lap_number=3, is_racing_lap=True),
            TyreWearPerLap(76, 76, 76, 76, lap_number=4, is_racing_lap=False),  # VSC lap
            TyreWearPerLap(72, 73, 70, 71, lap_number=5, is_racing_lap=True),
        ]
        self.total_laps = 10
        self.extrapolator = TyreWearExtrapolator(self.mixed_data, self.total_laps)

    def test_racing_laps_are_filtered_correctly(self):
        """Only racing laps should be used for predictions."""
        racing_laps = [lap for lap in self.mixed_data if lap.is_racing_lap]
        self.assertEqual(self.extrapolator.num_samples, len(racing_laps))

    def test_prediction_ignores_non_racing_laps(self):
        """Prediction should be based only on racing laps."""
        pred = self.extrapolator.getTyreWearPrediction(lap_number=10)
        self.assertIsInstance(pred, TyreWearPerLap)
        self.assertEqual(pred.lap_number, 10)

    def test_remaining_laps_ignores_non_racing_laps(self):
        """Remaining laps calculation should still work based on actual lap numbers."""
        self.assertEqual(self.extrapolator.remaining_laps, 5)  # last racing lap was lap 5

    def test_clear_and_add_with_mixed_laps(self):
        """Clearing and adding new laps with mixed types should still behave correctly."""
        self.extrapolator.clear()
        self.assertFalse(self.extrapolator.isDataSufficient())

        # Add only non-racing lap
        self.extrapolator.add(TyreWearPerLap(70, 70, 70, 70, lap_number=6, is_racing_lap=False))
        self.assertFalse(self.extrapolator.isDataSufficient())

        # Add first valid racing lap
        self.extrapolator.add(TyreWearPerLap(68, 69, 67, 68, lap_number=7, is_racing_lap=True))
        self.assertFalse(self.extrapolator.isDataSufficient())  # Still insufficient, only 1 racing lap

        # Add second valid racing lap
        self.extrapolator.add(TyreWearPerLap(66, 68, 65, 66, lap_number=8, is_racing_lap=True))
        self.assertTrue(self.extrapolator.isDataSufficient())

class TestTyreWearExtrapolatorWithMissingLaps(TestTyreWearPrediction):

    def test_missing_mid_lap(self):
        data = [
            TyreWearPerLap(1.0, 1.1, 1.2, 1.3, lap_number=10, is_racing_lap=True),
            # Missing lap 11
            TyreWearPerLap(1.5, 1.6, 1.7, 1.8, lap_number=12, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=15)

        self.assertTrue(extrap.isDataSufficient())
        pred = extrap.getTyreWearPrediction(15)

        self.assertIsNotNone(pred)
        self.assertEqual(pred.lap_number, 15)

    def test_missing_final_lap(self):
        data = [
            TyreWearPerLap(1.0, 1.1, 1.2, 1.3, lap_number=20, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=25)

        self.assertEqual(extrap.remaining_laps, 5)
        self.assertEqual(extrap.predicted_tyre_wear[-1].lap_number, 25)

    def test_racing_and_nonracing_with_gap(self):
        data = [
            TyreWearPerLap(1.0, 1.0, 1.0, 1.0, lap_number=5, is_racing_lap=True),
            TyreWearPerLap(1.2, 1.2, 1.2, 1.2, lap_number=6, is_racing_lap=False),
            # Missing lap 7
            TyreWearPerLap(1.5, 1.5, 1.5, 1.5, lap_number=8, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10)

        self.assertEqual(len(extrap.m_racing_data), 2)
        self.assertTrue(extrap.isDataSufficient())

    def test_insufficient_data_due_to_gaps(self):
        data = [
            TyreWearPerLap(1.0, 1.0, 1.0, 1.0, lap_number=3, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10)

        self.assertFalse(extrap.isDataSufficient())

    def test_recovery_after_missing_laps(self):
        data = [
            TyreWearPerLap(1.0, 1.0, 1.0, 1.0, lap_number=2, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=6)

        self.assertFalse(extrap.isDataSufficient())

        extrap.add(TyreWearPerLap(2.0, 2.0, 2.0, 2.0, lap_number=4, is_racing_lap=True))
        self.assertTrue(extrap.isDataSufficient())
        self.assertIsNotNone(extrap.getTyreWearPrediction(6))
