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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import CaptureSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestCaptureSettings(TestF1ConfigBase):
    """Test CaptureSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = CaptureSettings()
        self.assertFalse(settings.post_race_data_autosave)

    def test_boolean_validation(self):
        capture_true = CaptureSettings(post_race_data_autosave=True)
        self.assertTrue(capture_true.post_race_data_autosave)

        capture_false = CaptureSettings(post_race_data_autosave=False)
        self.assertFalse(capture_false.post_race_data_autosave)

        # Also test coercion from strings if you want
        capture_str_true = CaptureSettings(post_race_data_autosave="True")
        self.assertTrue(capture_str_true.post_race_data_autosave)

        capture_str_false = CaptureSettings(post_race_data_autosave="False")
        self.assertFalse(capture_str_false.post_race_data_autosave)

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            CaptureSettings(post_race_data_autosave="notaboolean")
