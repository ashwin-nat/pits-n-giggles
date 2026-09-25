# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import LapRecordingSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestLapRecordingSettings(TestF1ConfigBase):
    """Test LapRecordingSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = LapRecordingSettings()
        self.assertTrue(settings.enable)
        self.assertTrue(settings.record_other_cars)
        self.assertFalse(settings.record_in_spectator_mode)
        self.assertTrue(settings.record_in_race)
        self.assertTrue(settings.record_in_quali)
        self.assertFalse(settings.record_in_fp)
        self.assertFalse(settings.record_in_tt)

    def test_boolean_validation_enable(self):
        self.assertTrue(LapRecordingSettings(enable=True).enable)
        self.assertFalse(LapRecordingSettings(enable=False).enable)

        # Also test coercion from strings
        self.assertTrue(LapRecordingSettings(enable="True").enable)
        self.assertFalse(LapRecordingSettings(enable="False").enable)

    def test_boolean_validation_record_other_cars(self):
        self.assertTrue(LapRecordingSettings(record_other_cars=True).record_other_cars)
        self.assertFalse(LapRecordingSettings(record_other_cars=False).record_other_cars)

        self.assertTrue(LapRecordingSettings(record_other_cars="True").record_other_cars)
        self.assertFalse(LapRecordingSettings(record_other_cars="False").record_other_cars)

    def test_boolean_validation_record_in_spectator_mode(self):
        self.assertTrue(LapRecordingSettings(record_in_spectator_mode=True).record_in_spectator_mode)
        self.assertFalse(LapRecordingSettings(record_in_spectator_mode=False).record_in_spectator_mode)

        self.assertTrue(LapRecordingSettings(record_in_spectator_mode="True").record_in_spectator_mode)
        self.assertFalse(LapRecordingSettings(record_in_spectator_mode="False").record_in_spectator_mode)

    def test_boolean_validation_record_in_race(self):
        self.assertTrue(LapRecordingSettings(record_in_race=True).record_in_race)
        self.assertFalse(LapRecordingSettings(record_in_race=False).record_in_race)

        self.assertTrue(LapRecordingSettings(record_in_race="True").record_in_race)
        self.assertFalse(LapRecordingSettings(record_in_race="False").record_in_race)

    def test_boolean_validation_record_in_quali(self):
        self.assertTrue(LapRecordingSettings(record_in_quali=True).record_in_quali)
        self.assertFalse(LapRecordingSettings(record_in_quali=False).record_in_quali)

        self.assertTrue(LapRecordingSettings(record_in_quali="True").record_in_quali)
        self.assertFalse(LapRecordingSettings(record_in_quali="False").record_in_quali)

    def test_boolean_validation_record_in_fp(self):
        self.assertTrue(LapRecordingSettings(record_in_fp=True).record_in_fp)
        self.assertFalse(LapRecordingSettings(record_in_fp=False).record_in_fp)

        self.assertTrue(LapRecordingSettings(record_in_fp="True").record_in_fp)
        self.assertFalse(LapRecordingSettings(record_in_fp="False").record_in_fp)

    def test_boolean_validation_record_in_tt(self):
        self.assertTrue(LapRecordingSettings(record_in_tt=True).record_in_tt)
        self.assertFalse(LapRecordingSettings(record_in_tt=False).record_in_tt)

        self.assertTrue(LapRecordingSettings(record_in_tt="True").record_in_tt)
        self.assertFalse(LapRecordingSettings(record_in_tt="False").record_in_tt)

    def test_invalid_type_raises(self):
        with self.assertRaises(ValidationError):
            LapRecordingSettings(enable="notaboolean")

        with self.assertRaises(ValidationError):
            LapRecordingSettings(record_other_cars="notaboolean")

        with self.assertRaises(ValidationError):
            LapRecordingSettings(record_in_spectator_mode="notaboolean")

        with self.assertRaises(ValidationError):
            LapRecordingSettings(record_in_race="notaboolean")

        with self.assertRaises(ValidationError):
            LapRecordingSettings(record_in_quali="notaboolean")

        with self.assertRaises(ValidationError):
            LapRecordingSettings(record_in_fp="notaboolean")

        with self.assertRaises(ValidationError):
            LapRecordingSettings(record_in_tt="notaboolean")
