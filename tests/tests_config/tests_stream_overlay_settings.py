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


from lib.config import StreamOverlaySettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------


class TestStreamOverlaySettings(TestF1ConfigBase):
    """Test StreamOverlaySettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = StreamOverlaySettings()
        self.assertFalse(settings.show_sample_data_at_start)
        self.assertEqual(settings.stream_overlay_update_interval_ms, 100)

    def test_sample_data_at_start_validation(self):
        # Accept explicit True
        settings = StreamOverlaySettings(show_sample_data_at_start=True)
        self.assertTrue(settings.show_sample_data_at_start)

        # Accept explicit False
        settings = StreamOverlaySettings(show_sample_data_at_start=False)
        self.assertFalse(settings.show_sample_data_at_start)

        # Invalid types should raise validation errors
        with self.assertRaises(ValidationError):
            StreamOverlaySettings(show_sample_data_at_start="notabool")

        with self.assertRaises(ValidationError):
            StreamOverlaySettings(show_sample_data_at_start=123)

    def test_update_interval_validation(self):
        """Test update interval must be positive and greater than 50ms"""
        settings = StreamOverlaySettings(stream_overlay_update_interval_ms=100)
        self.assertEqual(settings.stream_overlay_update_interval_ms, 100)

        with self.assertRaises(ValidationError):
            StreamOverlaySettings(stream_overlay_update_interval_ms=0)

        with self.assertRaises(ValidationError):
            StreamOverlaySettings(stream_overlay_update_interval_ms=49)

        with self.assertRaises(ValidationError):
            StreamOverlaySettings(stream_overlay_update_interval_ms="notanumber")
