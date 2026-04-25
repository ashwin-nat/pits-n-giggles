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
from unittest.mock import MagicMock

from tests_base import F1TelemetryUnitTestsBase

from lib.tyre_wear_extrapolator import TyreWearExtrapolator, TyreWearPerLap
from lib.tyre_wear_extrapolator.simple_linear_regression import SimpleLinearRegression
from lib.f1_types.packet_1_session_data import WeatherForecastSample


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

    def test_enforce_monotonicity_clamps_decreasing_tyre_wear(self):
        self.extrapolator.m_logger = MagicMock()
        self.extrapolator.m_predicted_tyre_wear = [
            TyreWearPerLap(50.0, 51.0, 52.0, 53.0, lap_number=5),
            TyreWearPerLap(49.0, 48.0, 52.0, 52.5, lap_number=6),
            TyreWearPerLap(48.5, 48.0, 51.0, 52.4, lap_number=7),
        ]

        self.extrapolator._enforce_monotonicity()

        lap6 = self.extrapolator.m_predicted_tyre_wear[1]
        lap7 = self.extrapolator.m_predicted_tyre_wear[2]

        # lap6: FL/FR/RR should be clamped to lap5 values; RL unchanged.
        self.assertEqual(lap6.fl_tyre_wear, 50.0)
        self.assertEqual(lap6.fr_tyre_wear, 51.0)
        self.assertEqual(lap6.rl_tyre_wear, 52.0)
        self.assertEqual(lap6.rr_tyre_wear, 53.0)

        # lap7 should be clamped against already-adjusted lap6.
        self.assertEqual(lap7.fl_tyre_wear, 50.0)
        self.assertEqual(lap7.fr_tyre_wear, 51.0)
        self.assertEqual(lap7.rl_tyre_wear, 52.0)
        self.assertEqual(lap7.rr_tyre_wear, 53.0)

        # Violations: lap6 (FL, FR, RR) + lap7 (FL, FR, RL, RR) = 7 warnings.
        self.assertEqual(self.extrapolator.m_logger.warning.call_count, 7)

    def test_enforce_monotonicity_keeps_valid_sequence_unchanged(self):
        self.extrapolator.m_logger = MagicMock()
        self.extrapolator.m_predicted_tyre_wear = [
            TyreWearPerLap(10.0, 11.0, 12.0, 13.0, lap_number=5),
            TyreWearPerLap(10.0, 11.5, 12.0, 13.1, lap_number=6),
            TyreWearPerLap(10.2, 11.5, 12.8, 13.2, lap_number=7),
        ]

        self.extrapolator._enforce_monotonicity()

        self.assertEqual(self.extrapolator.m_predicted_tyre_wear[0].fl_tyre_wear, 10.0)
        self.assertEqual(self.extrapolator.m_predicted_tyre_wear[1].fr_tyre_wear, 11.5)
        self.assertEqual(self.extrapolator.m_predicted_tyre_wear[2].rl_tyre_wear, 12.8)
        self.assertEqual(self.extrapolator.m_predicted_tyre_wear[2].rr_tyre_wear, 13.2)
        self.extrapolator.m_logger.warning.assert_not_called()

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


class TestTyreWearExtrapolatorWithSCGaps(TestTyreWearPrediction):
    """Test that SC-induced lap number gaps don't dilute the regression slope."""

    def test_sc_gap_does_not_dilute_slope(self):
        """Racing laps 1-3, then SC on 4-6, then racing lap 7.
        Without sequential re-indexing, the slope would be diluted by the gap.
        """
        data = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(12.0, 12.0, 12.0, 12.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=3, is_racing_lap=True),
            # SC laps 4-6 (non-racing) are excluded from regression
            TyreWearPerLap(14.5, 14.5, 14.5, 14.5, lap_number=4, is_racing_lap=False),
            TyreWearPerLap(14.8, 14.8, 14.8, 14.8, lap_number=5, is_racing_lap=False),
            TyreWearPerLap(15.0, 15.0, 15.0, 15.0, lap_number=6, is_racing_lap=False),
            TyreWearPerLap(16.0, 16.0, 16.0, 16.0, lap_number=7, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10)

        # The 4 racing laps are at wear 10, 12, 14, 16 => slope should be ~2.0/racing-lap
        self.assertAlmostEqual(extrap.fl_rate, 2.0, delta=0.01)
        self.assertAlmostEqual(extrap.fr_rate, 2.0, delta=0.01)

        # Prediction for final lap should reflect the true racing slope, not a diluted one
        pred = extrap.getTyreWearPrediction(10)
        self.assertIsNotNone(pred)
        # 4 racing laps so far + 3 remaining => index 6 => 2.0*6 + 10.0 = 22.0
        self.assertAlmostEqual(pred.fl_tyre_wear, 22.0, delta=0.5)

    def test_mixed_rain_laps_still_used_for_regression(self):
        """Rain laps marked as racing_lap=True have lower wear.
        The regression will blend them, but sequential indexing ensures no gap dilution.
        """
        data = [
            # Dry laps with ~3%/lap wear rate
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, is_racing_lap=True),
            # Rain laps with ~1%/lap wear rate (still racing laps)
            TyreWearPerLap(12.0, 12.0, 12.0, 12.0, lap_number=4, is_racing_lap=True),
            TyreWearPerLap(13.0, 13.0, 13.0, 13.0, lap_number=5, is_racing_lap=True),
            # Back to dry
            TyreWearPerLap(16.0, 16.0, 16.0, 16.0, lap_number=6, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10)

        self.assertTrue(extrap.isDataSufficient())
        pred = extrap.getTyreWearPrediction(10)
        self.assertIsNotNone(pred)
        # Predictions should still extrapolate reasonable values
        self.assertGreater(pred.fl_tyre_wear, 16.0)

    def test_consecutive_racing_laps_produce_same_result_as_before(self):
        """When all laps are consecutive racing laps, sequential indexing
        matches actual lap numbers (0-based vs 1-based offset changes intercept but not slope).
        """
        data = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=5)

        # Slope should be 4.0 per racing lap regardless of indexing scheme
        self.assertAlmostEqual(extrap.fl_rate, 4.0, delta=0.01)

        pred = extrap.getTyreWearPrediction(5)
        self.assertIsNotNone(pred)
        # Index 4 (5th racing lap) => 4.0*4 + 10.0 = 26.0
        self.assertAlmostEqual(pred.fl_tyre_wear, 26.0, delta=0.5)


class TestTyreWearExtrapolatorSlidingWindow(TestTyreWearPrediction):
    """Test that the sliding window limits regression to the N most recent
    racing laps, allowing the model to adapt to weather transitions."""

    @staticmethod
    def _build_dry_then_wet_data() -> List[TyreWearPerLap]:
        """10 dry racing laps (~3 %/lap) followed by 8 wet laps (~1 %/lap)."""
        data: List[TyreWearPerLap] = []
        wear = 5.0
        for lap in range(1, 11):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))
            wear += 3.0
        for lap in range(11, 19):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))
            wear += 1.0
        return data

    @staticmethod
    def _build_wet_then_dry_data() -> List[TyreWearPerLap]:
        """10 wet racing laps (~1 %/lap) followed by 8 dry laps (~3 %/lap)."""
        data: List[TyreWearPerLap] = []
        wear = 2.0
        for lap in range(1, 11):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))
            wear += 1.0
        for lap in range(11, 19):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))
            wear += 3.0
        return data

    def test_dry_to_wet_transition_with_sliding_window(self):
        """After 8 wet laps with window_size=8 the regression slope should
        reflect the wet wear rate (~1 %/lap), not a dry/wet average."""
        data = self._build_dry_then_wet_data()
        total_laps = 25

        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps, window_size=8)

        self.assertTrue(extrap.isDataSufficient())
        # The window contains only wet laps → slope ≈ 1.0
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)
        self.assertAlmostEqual(extrap.rr_rate, 1.0, delta=0.1)

        pred = extrap.getTyreWearPrediction(total_laps)
        self.assertIsNotNone(pred)
        # Regression fitted on 8 wet points (indices 0-7).
        # Slope 1.0, intercept 35.0 → predict(14) = 49.0 for lap 25.
        self.assertAlmostEqual(pred.fl_tyre_wear, 49.0, delta=1.0)

    def test_dry_to_wet_without_window_has_higher_slope(self):
        """Without sliding window the slope averages over the whole stint,
        producing a higher-than-wet-rate prediction — the bug we're fixing."""
        data = self._build_dry_then_wet_data()
        total_laps = 25

        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps, window_size=None)

        # Slope averaged over dry + wet → clearly above the pure wet rate.
        self.assertGreater(extrap.fl_rate, 1.5)

    def test_wet_to_dry_transition_with_sliding_window(self):
        """After 8 dry laps with window_size=8 the regression should track
        the dry wear rate (~3 %/lap), avoiding a dangerously low prediction."""
        data = self._build_wet_then_dry_data()
        total_laps = 25

        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps, window_size=8)

        self.assertTrue(extrap.isDataSufficient())
        # The window contains only dry laps → slope ≈ 3.0
        self.assertAlmostEqual(extrap.fl_rate, 3.0, delta=0.1)
        self.assertAlmostEqual(extrap.rl_rate, 3.0, delta=0.1)

        pred = extrap.getTyreWearPrediction(total_laps)
        self.assertIsNotNone(pred)

    def test_wet_to_dry_without_window_has_lower_slope(self):
        """Without sliding window the slope averages wet + dry data,
        producing a lower-than-dry-rate prediction — potentially dangerous."""
        data = self._build_wet_then_dry_data()
        total_laps = 25

        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps, window_size=None)

        # Slope averaged → clearly below the pure dry rate.
        self.assertLess(extrap.fl_rate, 2.5)

    def test_window_size_none_preserves_old_behavior(self):
        """window_size=None must produce identical results to the default
        (no window_size argument)."""
        data = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3, is_racing_lap=True),
        ]
        extrap_default = TyreWearExtrapolator(initial_data=list(data), total_laps=5)
        extrap_none = TyreWearExtrapolator(initial_data=list(data), total_laps=5, window_size=None)

        self.assertAlmostEqual(extrap_default.fl_rate, extrap_none.fl_rate)
        self.assertAlmostEqual(
            extrap_default.getTyreWearPrediction(5).fl_tyre_wear,
            extrap_none.getTyreWearPrediction(5).fl_tyre_wear,
        )

    def test_window_size_zero_preserves_old_behavior(self):
        """window_size=0 is an alias for 'use all data' — same as None."""
        data = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3, is_racing_lap=True),
        ]
        extrap_none = TyreWearExtrapolator(initial_data=list(data), total_laps=5, window_size=None)
        extrap_zero = TyreWearExtrapolator(initial_data=list(data), total_laps=5, window_size=0)

        self.assertAlmostEqual(extrap_none.fl_rate, extrap_zero.fl_rate)
        self.assertAlmostEqual(
            extrap_none.getTyreWearPrediction(5).fl_tyre_wear,
            extrap_zero.getTyreWearPrediction(5).fl_tyre_wear,
        )

    def test_window_adapts_incrementally_via_add(self):
        """Simulate a live race: start dry, rain arrives, add laps one by one.
        The window should progressively flush out the dry data."""
        total_laps = 20
        # Start with 4 dry laps (~3 %/lap)
        data = [
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, is_racing_lap=True),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps, window_size=4)

        # At this point, 4 dry laps in window → slope ≈ 3.0
        self.assertAlmostEqual(extrap.fl_rate, 3.0, delta=0.1)

        # Rain arrives: add 4 wet laps (~1 %/lap)
        wear = 14.0
        for lap in range(5, 9):
            wear += 1.0
            extrap.add(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))

        # After 4 wet laps the window is fully flushed → slope ≈ 1.0
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)

    def test_dry_to_wet_transition_with_w6(self):
        """With the production default window_size=6, a dry→wet transition
        should be tracked once enough wet laps fill the window."""
        # 6 dry racing laps (~3 %/lap) then 6 wet racing laps (~1 %/lap)
        data: List[TyreWearPerLap] = []
        wear = 5.0
        for lap in range(1, 7):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))
            wear += 3.0
        for lap in range(7, 13):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap, is_racing_lap=True))
            wear += 1.0
        total_laps = 20

        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps, window_size=6)

        self.assertTrue(extrap.isDataSufficient())
        # Window covers only the 6 wet laps → slope ≈ 1.0
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)
        self.assertAlmostEqual(extrap.rr_rate, 1.0, delta=0.1)

        pred = extrap.getTyreWearPrediction(total_laps)
        self.assertIsNotNone(pred)
        # Verify prediction is based on wet rate, not the dry/wet average
        # Last recorded wear = 28.0 at lap 12, predict to lap 20 at ~1 /lap
        self.assertAlmostEqual(pred.fl_tyre_wear, 36.0, delta=1.5)

    def test_exact_window_size_uses_all_data(self):
        """Edge case: len(racing_data) == window_size.
        The `>` condition does NOT trigger, so all data is used — which is
        identical to the last N entries anyway."""
        data = [
            TyreWearPerLap(5.0,  5.0,  5.0,  5.0,  lap_number=1, is_racing_lap=True),
            TyreWearPerLap(7.0,  7.0,  7.0,  7.0,  lap_number=2, is_racing_lap=True),
            TyreWearPerLap(9.0,  9.0,  9.0,  9.0,  lap_number=3, is_racing_lap=True),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=4, is_racing_lap=True),
            TyreWearPerLap(13.0, 13.0, 13.0, 13.0, lap_number=5, is_racing_lap=True),
            TyreWearPerLap(15.0, 15.0, 15.0, 15.0, lap_number=6, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10, window_size=6)

        # All 6 laps should be used — slope = 2.0
        self.assertAlmostEqual(extrap.fl_rate, 2.0, delta=0.01)
        self.assertEqual(extrap.num_samples, 6)
        self.assertEqual(extrap.m_regression_sample_count, 6)

        pred = extrap.getTyreWearPrediction(10)
        self.assertIsNotNone(pred)
        # Index 9 (10th racing-lap equivalent): 2.0*9 + 5.0 = 23.0
        self.assertAlmostEqual(pred.fl_tyre_wear, 23.0, delta=0.5)

    def test_window_smaller_than_data_uses_only_tail(self):
        """When data exceeds window_size, only the tail is used for regression."""
        data = [
            TyreWearPerLap(5.0,  5.0,  5.0,  5.0,  lap_number=1, is_racing_lap=True),
            TyreWearPerLap(8.0,  8.0,  8.0,  8.0,  lap_number=2, is_racing_lap=True),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, is_racing_lap=True),
            # Tail (window_size=2): only these two should be used
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, is_racing_lap=True),
            TyreWearPerLap(15.0, 15.0, 15.0, 15.0, lap_number=5, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10, window_size=2)

        # Regression on [14, 15] at indices [0, 1] → slope = 1.0
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.01)
        # But total racing laps collected is still 5
        self.assertEqual(extrap.num_samples, 5)


class TestTyreWearExtrapolatorWeatherSegmentation(TestTyreWearPrediction):
    """Test weather-aware segmentation: dry/wet grouping, fallback logic,
    and backward compatibility with legacy data (weather_id=None)."""

    # Weather enum constants
    CLEAR = WeatherForecastSample.WeatherCondition.CLEAR
    LIGHT_CLOUD = WeatherForecastSample.WeatherCondition.LIGHT_CLOUD
    OVERCAST = WeatherForecastSample.WeatherCondition.OVERCAST
    LIGHT_RAIN = WeatherForecastSample.WeatherCondition.LIGHT_RAIN
    HEAVY_RAIN = WeatherForecastSample.WeatherCondition.HEAVY_RAIN
    STORM = WeatherForecastSample.WeatherCondition.STORM

    def test_weather_group_mapping(self):
        """Dry = {0,1,2}, Wet = {3,4,5,6}."""
        WC = WeatherForecastSample.WeatherCondition
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.CLEAR), "dry")
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.LIGHT_CLOUD), "dry")
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.OVERCAST), "dry")
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.LIGHT_RAIN), "wet")
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.HEAVY_RAIN), "wet")
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.STORM), "wet")
        self.assertEqual(TyreWearExtrapolator._weather_group(WC.THUNDERSTORM), "wet")
        self.assertIsNone(TyreWearExtrapolator._weather_group(None))

    def test_all_none_weather_backward_compat(self):
        """Legacy data without weather_id must behave identically to before."""
        data = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, is_racing_lap=True),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2, is_racing_lap=True),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3, is_racing_lap=True),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=5)

        self.assertAlmostEqual(extrap.fl_rate, 4.0, delta=0.01)
        pred = extrap.getTyreWearPrediction(5)
        self.assertIsNotNone(pred)
        self.assertAlmostEqual(pred.fl_tyre_wear, 26.0, delta=0.5)

    def test_segmentation_splits_on_weather_change(self):
        """Dry→Wet in mid-race (all racing laps) produces separate segments."""
        data = [
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(12.0, 12.0, 12.0, 12.0, lap_number=4, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(13.0, 13.0, 13.0, 13.0, lap_number=5, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=6, weather_id=self.HEAVY_RAIN),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=10)

        # Should have 2 segments: [dry R, dry R, dry R], [wet R, wet R, wet R]
        self.assertEqual(len(extrap.m_intervals), 2)
        self.assertEqual(len(extrap.m_intervals[0]), 3)
        self.assertEqual(len(extrap.m_intervals[1]), 3)

    def test_dry_to_wet_regression_uses_wet_segment(self):
        """With 3+ wet racing laps, regression uses only wet data."""
        data = [
            # 5 dry laps (~3%/lap)
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, weather_id=self.LIGHT_CLOUD),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=5, weather_id=self.OVERCAST),
            # 4 wet laps (~1%/lap)
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=6, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(19.0, 19.0, 19.0, 19.0, lap_number=7, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(20.0, 20.0, 20.0, 20.0, lap_number=8, weather_id=self.HEAVY_RAIN),
            TyreWearPerLap(21.0, 21.0, 21.0, 21.0, lap_number=9, weather_id=self.HEAVY_RAIN),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=15)

        # Regression should be based on wet data → slope ≈ 1.0
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)

    def test_wet_to_dry_regression_uses_dry_segment(self):
        """After switching back to dry with 3+ laps, dry data is used."""
        data = [
            # 4 wet laps (~1%/lap)
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(6.0, 6.0, 6.0, 6.0, lap_number=2, weather_id=self.HEAVY_RAIN),
            TyreWearPerLap(7.0, 7.0, 7.0, 7.0, lap_number=3, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=4, weather_id=self.LIGHT_RAIN),
            # 4 dry laps (~3%/lap)
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=5, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=6, weather_id=self.CLEAR),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=7, weather_id=self.CLEAR),
            TyreWearPerLap(20.0, 20.0, 20.0, 20.0, lap_number=8, weather_id=self.CLEAR),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=15)

        # Regression should be based on dry data → slope ≈ 3.0
        self.assertAlmostEqual(extrap.fl_rate, 3.0, delta=0.1)

    def test_short_wet_segment_falls_back_to_all_data(self):
        """With < 3 wet racing laps, fallback to all data (sliding window handles it)."""
        data = [
            # 5 dry laps (~3%/lap)
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, weather_id=self.CLEAR),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=5, weather_id=self.CLEAR),
            # Only 2 wet laps — below threshold
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=6, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(19.0, 19.0, 19.0, 19.0, lap_number=7, weather_id=self.LIGHT_RAIN),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=15)

        # Fallback: all 7 racing laps used. Slope is a mix of dry+wet.
        # Not purely 3.0 or 1.0 — somewhere in between.
        self.assertGreater(extrap.fl_rate, 1.0)
        self.assertLess(extrap.fl_rate, 3.0)
        self.assertTrue(extrap.isDataSufficient())

    def test_short_segment_then_enough_data_switches(self):
        """Add laps incrementally: once 3 wet laps accumulate, regression should adapt."""
        total_laps = 20
        data = [
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, weather_id=self.CLEAR),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=5, weather_id=self.CLEAR),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=total_laps)
        self.assertAlmostEqual(extrap.fl_rate, 3.0, delta=0.1)

        # Add 2 wet laps — still in fallback
        extrap.add(TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=6, weather_id=self.LIGHT_RAIN))
        extrap.add(TyreWearPerLap(19.0, 19.0, 19.0, 19.0, lap_number=7, weather_id=self.HEAVY_RAIN))
        # Slope is still mixed
        self.assertGreater(extrap.fl_rate, 1.0)

        # Add 3rd wet lap — threshold reached, regression switches to wet-only
        extrap.add(TyreWearPerLap(20.0, 20.0, 20.0, 20.0, lap_number=8, weather_id=self.HEAVY_RAIN))
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)

    def test_no_weather_segment_break_within_same_group(self):
        """Different weather IDs in the same group (e.g. Clear→Overcast) must NOT cause a break."""
        data = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2, weather_id=self.LIGHT_CLOUD),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3, weather_id=self.OVERCAST),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=5)

        # All dry — single segment, slope = 4.0
        self.assertEqual(len(extrap.m_intervals), 1)
        self.assertAlmostEqual(extrap.fl_rate, 4.0, delta=0.01)

    def test_weather_and_sc_combined_segmentation(self):
        """Weather + SC changes should both cause segment breaks."""
        data = [
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, is_racing_lap=True, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, is_racing_lap=True, weather_id=self.CLEAR),
            TyreWearPerLap(8.5, 8.5, 8.5, 8.5, lap_number=3, is_racing_lap=False, weather_id=self.CLEAR),  # SC
            TyreWearPerLap(9.0, 9.0, 9.0, 9.0, lap_number=4, is_racing_lap=True, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=5, is_racing_lap=True, weather_id=self.HEAVY_RAIN),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=6, is_racing_lap=True, weather_id=self.HEAVY_RAIN),
        ]
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=15)

        # Segments: [dry racing 1-2], [SC dry 3], [wet racing 4-6]
        self.assertEqual(len(extrap.m_intervals), 3)
        self.assertTrue(extrap.isDataSufficient())

    def test_toJSON_includes_weather_id(self):
        """TyreWearPerLap.toJSON() must export weather-id."""
        lap = TyreWearPerLap(90.0, 85.0, 80.0, 75.0, lap_number=5, weather_id=self.LIGHT_RAIN)
        json_data = lap.toJSON()
        self.assertEqual(json_data["weather-id"], self.LIGHT_RAIN)

    def test_toJSON_weather_id_none(self):
        """Legacy data without weather_id exports None."""
        lap = TyreWearPerLap(90.0, 85.0, 80.0, 75.0, lap_number=5)
        json_data = lap.toJSON()
        self.assertIsNone(json_data["weather-id"])

    def test_weather_segmentation_with_sliding_window(self):
        """Weather filter runs before sliding window. Window operates on
        weather-filtered data."""
        data: List[TyreWearPerLap] = []
        # 5 dry laps (~3%/lap)
        wear = 5.0
        for lap in range(1, 6):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap,
                                       is_racing_lap=True, weather_id=self.CLEAR))
            wear += 3.0
        # 8 wet laps (~1%/lap) — more than window_size=6
        for lap in range(6, 14):
            data.append(TyreWearPerLap(wear, wear, wear, wear, lap_number=lap,
                                       is_racing_lap=True, weather_id=self.LIGHT_RAIN))
            wear += 1.0
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=20, window_size=6)

        # 8 wet laps → filtered to wet (8 laps) → window slices to last 6
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)


class TestTyreWearExtrapolatorWeatherAwareFlag(TestTyreWearPrediction):
    """Test that weather_aware=False disables weather-group filtering and
    uses all racing laps for regression (legacy behaviour)."""

    CLEAR = WeatherForecastSample.WeatherCondition.CLEAR
    LIGHT_RAIN = WeatherForecastSample.WeatherCondition.LIGHT_RAIN
    HEAVY_RAIN = WeatherForecastSample.WeatherCondition.HEAVY_RAIN

    def test_default_is_weather_aware(self):
        """weather_aware defaults to True — flag is stored correctly."""
        extrap = TyreWearExtrapolator(initial_data=[], total_laps=10)
        self.assertTrue(extrap.m_weather_aware)

    def test_flag_stored_false(self):
        """weather_aware=False is stored on the instance."""
        extrap = TyreWearExtrapolator(initial_data=[], total_laps=10, weather_aware=False)
        self.assertFalse(extrap.m_weather_aware)

    def test_disabled_uses_all_racing_laps(self):
        """With weather_aware=False, regression uses all racing laps regardless
        of weather group — slope is a blend of dry and wet data."""
        data = [
            # 5 dry laps (~3%/lap)
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, weather_id=self.CLEAR),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=5, weather_id=self.CLEAR),
            # 4 wet laps (~1%/lap)
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=6, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(19.0, 19.0, 19.0, 19.0, lap_number=7, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(20.0, 20.0, 20.0, 20.0, lap_number=8, weather_id=self.HEAVY_RAIN),
            TyreWearPerLap(21.0, 21.0, 21.0, 21.0, lap_number=9, weather_id=self.HEAVY_RAIN),
        ]

        extrap_aware = TyreWearExtrapolator(initial_data=list(data), total_laps=15)
        extrap_legacy = TyreWearExtrapolator(initial_data=list(data), total_laps=15, weather_aware=False)

        # Weather-aware: only 4 wet laps → slope ≈ 1.0
        self.assertAlmostEqual(extrap_aware.fl_rate, 1.0, delta=0.1)

        # Legacy: all 9 laps blended → slope clearly above 1.0
        self.assertGreater(extrap_legacy.fl_rate, 1.5)

    def test_disabled_short_wet_segment_does_not_fall_back(self):
        """With weather_aware=False, even a short wet segment (< MIN_LAPS)
        does NOT fall back — all racing data is always used."""
        data = [
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, weather_id=self.CLEAR),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=5, weather_id=self.CLEAR),
            # Only 2 wet laps — below threshold, weather-aware would fall back
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=6, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(19.0, 19.0, 19.0, 19.0, lap_number=7, weather_id=self.LIGHT_RAIN),
        ]

        extrap_aware = TyreWearExtrapolator(initial_data=list(data), total_laps=15)
        extrap_legacy = TyreWearExtrapolator(initial_data=list(data), total_laps=15, weather_aware=False)

        # Both use all 7 laps when weather_aware falls back — rates should match
        self.assertAlmostEqual(extrap_aware.fl_rate, extrap_legacy.fl_rate, delta=0.01)

    def test_disabled_matches_no_weather_data(self):
        """weather_aware=False on data with explicit weather IDs produces the
        same result as data with no weather IDs at all (true legacy behaviour)."""
        data_with_weather = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3, weather_id=self.CLEAR),
        ]
        data_no_weather = [
            TyreWearPerLap(10.0, 10.0, 10.0, 10.0, lap_number=1),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=2),
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=3),
        ]

        extrap_legacy = TyreWearExtrapolator(initial_data=data_with_weather, total_laps=5, weather_aware=False)
        extrap_no_weather = TyreWearExtrapolator(initial_data=data_no_weather, total_laps=5)

        self.assertAlmostEqual(extrap_legacy.fl_rate, extrap_no_weather.fl_rate, delta=0.01)
        self.assertAlmostEqual(
            extrap_legacy.getTyreWearPrediction(5).fl_tyre_wear,
            extrap_no_weather.getTyreWearPrediction(5).fl_tyre_wear,
            delta=0.01,
        )

    def test_disabled_with_sliding_window(self):
        """weather_aware=False + window_size: sliding window still applies,
        but on the full racing dataset (no weather filter)."""
        data = [
            # 5 dry laps (~3%/lap)
            TyreWearPerLap(5.0, 5.0, 5.0, 5.0, lap_number=1, weather_id=self.CLEAR),
            TyreWearPerLap(8.0, 8.0, 8.0, 8.0, lap_number=2, weather_id=self.CLEAR),
            TyreWearPerLap(11.0, 11.0, 11.0, 11.0, lap_number=3, weather_id=self.CLEAR),
            TyreWearPerLap(14.0, 14.0, 14.0, 14.0, lap_number=4, weather_id=self.CLEAR),
            TyreWearPerLap(17.0, 17.0, 17.0, 17.0, lap_number=5, weather_id=self.CLEAR),
            # 4 wet laps (~1%/lap)
            TyreWearPerLap(18.0, 18.0, 18.0, 18.0, lap_number=6, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(19.0, 19.0, 19.0, 19.0, lap_number=7, weather_id=self.LIGHT_RAIN),
            TyreWearPerLap(20.0, 20.0, 20.0, 20.0, lap_number=8, weather_id=self.HEAVY_RAIN),
            TyreWearPerLap(21.0, 21.0, 21.0, 21.0, lap_number=9, weather_id=self.HEAVY_RAIN),
        ]
        # window_size=4 slices the last 4 laps (all wet, ~1%/lap)
        extrap = TyreWearExtrapolator(initial_data=data, total_laps=15, weather_aware=False, window_size=4)

        # Even without weather filtering, the window isolates the 4 wet laps → slope ≈ 1.0
        self.assertAlmostEqual(extrap.fl_rate, 1.0, delta=0.1)

