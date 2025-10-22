# ----------------------------------------------------------------------------------------------------------------------
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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic import ValidationError

from lib.config import HudSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestHudSettings(TestF1ConfigBase):
    """Test LoggingSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = HudSettings()
        self.assertEqual(settings.enabled, False)

    def test_enabled_validation(self):
        """Test valid and invalid log_file_size values"""
        # Valid value
        enabled = True
        hud_settings = HudSettings(enabled=enabled)
        self.assertEqual(hud_settings.enabled, enabled)

        with self.assertRaises(ValidationError):
            HudSettings(enabled=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(enabled="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(enabled=420)
