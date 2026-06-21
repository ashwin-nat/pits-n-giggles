# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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
import sys

from pydantic import ValidationError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import PngSettings, PredictionSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------


class TestPredictionSettings(TestF1ConfigBase):
    """Test PredictionSettings model"""

    def test_default_values(self):
        """Defaults: weather-aware off, no sliding window."""
        s = PredictionSettings()
        self.assertFalse(s.weather_aware_prediction)
        self.assertIsNone(s.tyre_wear_window_size)

    def test_weather_aware_prediction_true(self):
        s = PredictionSettings(weather_aware_prediction=True)
        self.assertTrue(s.weather_aware_prediction)

    def test_weather_aware_prediction_false(self):
        s = PredictionSettings(weather_aware_prediction=False)
        self.assertFalse(s.weather_aware_prediction)

    def test_weather_aware_prediction_invalid_type(self):
        with self.assertRaises(ValidationError):
            PredictionSettings(weather_aware_prediction=[1, 2, 3])

    def test_tyre_wear_window_size_valid(self):
        s = PredictionSettings(tyre_wear_window_size=6)
        self.assertEqual(s.tyre_wear_window_size, 6)

    def test_tyre_wear_window_size_none(self):
        s = PredictionSettings(tyre_wear_window_size=None)
        self.assertIsNone(s.tyre_wear_window_size)

    def test_tyre_wear_window_size_minimum(self):
        """ge=2: 2 is valid, 1 is not."""
        s = PredictionSettings(tyre_wear_window_size=2)
        self.assertEqual(s.tyre_wear_window_size, 2)

        with self.assertRaises(ValidationError):
            PredictionSettings(tyre_wear_window_size=1)

    def test_tyre_wear_window_size_invalid_type(self):
        with self.assertRaises(ValidationError):
            PredictionSettings(tyre_wear_window_size="six")

    def test_both_flags_set(self):
        s = PredictionSettings(weather_aware_prediction=True, tyre_wear_window_size=8)
        self.assertTrue(s.weather_aware_prediction)
        self.assertEqual(s.tyre_wear_window_size, 8)

    def test_harvest_power_window_size_default(self):
        """Default harvest power smoothing window is 15."""
        s = PredictionSettings()
        self.assertEqual(s.harvest_power_window_size, 15)

    def test_harvest_power_window_size_valid_values(self):
        """All supported SavGol window sizes are accepted."""
        for w in (9, 15, 21):
            s = PredictionSettings(harvest_power_window_size=w)
            self.assertEqual(s.harvest_power_window_size, w)

    def test_harvest_power_window_size_invalid_value(self):
        """Values outside the supported set are rejected."""
        for w in (0, 12, 25):
            with self.assertRaises(ValidationError):
                PredictionSettings(harvest_power_window_size=w)

    def test_harvest_power_window_size_invalid_type(self):
        with self.assertRaises(ValidationError):
            PredictionSettings(harvest_power_window_size="big")

    def test_diff_weather_aware(self):
        s1 = PredictionSettings()
        s2 = PredictionSettings(weather_aware_prediction=True)
        self.assertTrue(s1.has_changed(s2))
        self.assertEqual(s1.diff(s2), {
            "weather_aware_prediction": {"old_value": False, "new_value": True}
        })

    def test_diff_window_size(self):
        s1 = PredictionSettings()
        s2 = PredictionSettings(tyre_wear_window_size=6)
        self.assertTrue(s1.has_changed(s2))
        self.assertEqual(s1.diff(s2), {
            "tyre_wear_window_size": {"old_value": None, "new_value": 6}
        })

    def test_diff_harvest_power_window_size(self):
        s1 = PredictionSettings()
        s2 = PredictionSettings(harvest_power_window_size=21)
        self.assertTrue(s1.has_changed(s2))
        self.assertEqual(s1.diff(s2), {
            "harvest_power_window_size": {"old_value": 15, "new_value": 21}
        })

    def test_diff_no_change(self):
        s1 = PredictionSettings(weather_aware_prediction=True, tyre_wear_window_size=4)
        s2 = PredictionSettings(weather_aware_prediction=True, tyre_wear_window_size=4)
        self.assertFalse(s1.has_changed(s2))
        self.assertEqual(s1.diff(s2), {})


class TestPngSettingsPrediction(TestF1ConfigBase):
    """Test that PredictionSettings is wired into PngSettings correctly."""

    def test_prediction_section_present(self):
        """PngSettings exposes a Prediction sub-model with correct defaults."""
        s = PngSettings()
        self.assertIsInstance(s.Prediction, PredictionSettings)
        self.assertFalse(s.Prediction.weather_aware_prediction)
        self.assertIsNone(s.Prediction.tyre_wear_window_size)

    def test_prediction_section_accepts_values(self):
        s = PngSettings(Prediction=PredictionSettings(
            weather_aware_prediction=True,
            tyre_wear_window_size=6,
        ))
        self.assertTrue(s.Prediction.weather_aware_prediction)
        self.assertEqual(s.Prediction.tyre_wear_window_size, 6)

    def test_prediction_diff_detected_by_png_settings(self):
        """A change inside Prediction is visible through the top-level diff."""
        s1 = PngSettings()
        s2 = PngSettings(Prediction=PredictionSettings(weather_aware_prediction=True))
        self.assertTrue(s1.has_changed(s2))
        d = s1.diff(s2)
        self.assertIn("Prediction", d)
        self.assertIn("weather_aware_prediction", d["Prediction"])

    def test_prediction_diff_field_filter(self):
        """diff() with Prediction:[] returns all changed fields in that section."""
        s1 = PngSettings()
        s2 = PngSettings(Prediction=PredictionSettings(
            weather_aware_prediction=True,
            tyre_wear_window_size=8,
        ))
        d = s1.diff(s2, {"Prediction": []})
        self.assertIn("Prediction", d)
        self.assertIn("weather_aware_prediction", d["Prediction"])
        self.assertIn("tyre_wear_window_size", d["Prediction"])

    def test_prediction_no_diff_when_unchanged(self):
        s1 = PngSettings()
        s2 = PngSettings()
        d = s1.diff(s2, {"Prediction": []})
        self.assertNotIn("Prediction", d)

    def test_png_settings_harvest_window_covered_by_prediction_diff(self):
        """Changing harvest_power_window_size is caught by the {"Prediction": []} diff
        the backend uses to decide on a restart."""
        s1 = PngSettings()
        s2 = PngSettings(Prediction=PredictionSettings(harvest_power_window_size=9))
        d = s1.diff(s2, {"Prediction": []})
        self.assertIn("Prediction", d)
        self.assertIn("harvest_power_window_size", d["Prediction"])
