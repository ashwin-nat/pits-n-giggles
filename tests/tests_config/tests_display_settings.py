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

from lib.config import DisplaySettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestDisplaySettings(TestF1ConfigBase):
    """Test DisplaySettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = DisplaySettings()
        self.assertEqual(settings.refresh_interval, 200)
        self.assertFalse(settings.disable_browser_autoload)
        self.assertEqual(settings.local_telemetry_rate, 5)
        self.assertEqual(settings.realtime_overlay_fps, 30)
        self.assertFalse(settings.use_cpu_acceleration)

    def test_refresh_interval_validation(self):
        """Test refresh interval must be positive"""
        settings = DisplaySettings(refresh_interval=100)
        self.assertEqual(settings.refresh_interval, 100)

        with self.assertRaises(ValidationError):
            DisplaySettings(refresh_interval=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(refresh_interval=-1)

    def test_disable_browser_autoload_boolean(self):
        # Default is False
        display = DisplaySettings()
        self.assertFalse(display.disable_browser_autoload)

        # True is accepted
        display = DisplaySettings(disable_browser_autoload=True)
        self.assertTrue(display.disable_browser_autoload)

        # String coercion works
        display = DisplaySettings(disable_browser_autoload="True")
        self.assertTrue(display.disable_browser_autoload)

        display = DisplaySettings(disable_browser_autoload="False")
        self.assertFalse(display.disable_browser_autoload)

    def test_invalid_disable_browser_autoload(self):
        with self.assertRaises(ValidationError):
            DisplaySettings(disable_browser_autoload="notaboolean")

    def test_local_telemetry_rate_validation(self):
        settings = DisplaySettings(local_telemetry_rate=5)
        self.assertEqual(settings.local_telemetry_rate, 5)

        # Boundary condition
        settings = DisplaySettings(local_telemetry_rate=1)
        self.assertEqual(settings.local_telemetry_rate, 1)

        with self.assertRaises(ValidationError):
            DisplaySettings(local_telemetry_rate=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(local_telemetry_rate=-1)

        with self.assertRaises(ValidationError):
            DisplaySettings(local_telemetry_rate=None)

        with self.assertRaises(ValidationError):
            DisplaySettings(local_telemetry_rate="notanumber")

    def test_realtime_overlay_fps_validation(self):
        settings = DisplaySettings(realtime_overlay_fps=30)
        self.assertEqual(settings.realtime_overlay_fps, 30)

        # Boundary condition
        settings = DisplaySettings(realtime_overlay_fps=1)
        self.assertEqual(settings.realtime_overlay_fps, 1)

        with self.assertRaises(ValidationError):
            DisplaySettings(realtime_overlay_fps=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(realtime_overlay_fps=-1)

        with self.assertRaises(ValidationError):
            DisplaySettings(realtime_overlay_fps=None)

        with self.assertRaises(ValidationError):
            DisplaySettings(realtime_overlay_fps="notanumber")

    def test_use_gpu_acceleration(self):
        settings = DisplaySettings(use_cpu_acceleration=True)
        self.assertTrue(settings.use_cpu_acceleration)

        settings = DisplaySettings(use_cpu_acceleration=False)
        self.assertFalse(settings.use_cpu_acceleration)

        with self.assertRaises(ValidationError):
            DisplaySettings(use_cpu_acceleration="notabool")

        with self.assertRaises(ValidationError):
            DisplaySettings(use_cpu_acceleration=123)
