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

from lib.config import AutoOpenDashboardMode, DisplaySettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestDisplaySettings(TestF1ConfigBase):
    """Test DisplaySettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = DisplaySettings()
        self.assertEqual(settings.refresh_interval, 200)
        self.assertEqual(settings.auto_open_dashboard, AutoOpenDashboardMode.HUB)
        self.assertEqual(settings.local_telemetry_rate, 5)
        self.assertEqual(settings.realtime_overlay_fps, 60)
        self.assertFalse(settings.use_cpu_acceleration)
        self.assertEqual(settings.wdt_timeout, 5.0)
        self.assertEqual(settings.save_viewer_poll_interval_secs, 10)

    def test_refresh_interval_validation(self):
        """Test refresh interval must be positive"""
        settings = DisplaySettings(refresh_interval=100)
        self.assertEqual(settings.refresh_interval, 100)

        with self.assertRaises(ValidationError):
            DisplaySettings(refresh_interval=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(refresh_interval=-1)

    def test_auto_open_dashboard_enum(self):
        # Default is Hub
        display = DisplaySettings()
        self.assertEqual(display.auto_open_dashboard, AutoOpenDashboardMode.HUB)

        # Each mode is accepted
        for mode in AutoOpenDashboardMode:
            display = DisplaySettings(auto_open_dashboard=mode)
            self.assertEqual(display.auto_open_dashboard, mode)

        # String value coercion works
        display = DisplaySettings(auto_open_dashboard="Disabled")
        self.assertEqual(display.auto_open_dashboard, AutoOpenDashboardMode.DISABLED)

    def test_invalid_auto_open_dashboard(self):
        with self.assertRaises(ValidationError):
            DisplaySettings(auto_open_dashboard="not_a_mode")

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

    def test_use_cpu_acceleration(self):
        settings = DisplaySettings(use_cpu_acceleration=True)
        self.assertTrue(settings.use_cpu_acceleration)

        settings = DisplaySettings(use_cpu_acceleration=False)
        self.assertFalse(settings.use_cpu_acceleration)

        with self.assertRaises(ValidationError):
            DisplaySettings(use_cpu_acceleration="notabool")

        with self.assertRaises(ValidationError):
            DisplaySettings(use_cpu_acceleration=123)

    def test_wdt_timeout_validation(self):
        settings = DisplaySettings(wdt_timeout=10.0)
        self.assertEqual(settings.wdt_timeout, 10.0)

        # Boundary condition
        settings = DisplaySettings(wdt_timeout=2.0)
        self.assertEqual(settings.wdt_timeout, 2.0)

        settings = DisplaySettings(wdt_timeout=None)
        self.assertIsNone(settings.wdt_timeout)

        with self.assertRaises(ValidationError):
            DisplaySettings(wdt_timeout=1.9)

        with self.assertRaises(ValidationError):
            DisplaySettings(wdt_timeout=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(wdt_timeout=-1)

        with self.assertRaises(ValidationError):
            DisplaySettings(wdt_timeout="notanumber")

    def test_save_viewer_poll_interval_secs_validation(self):
        settings = DisplaySettings(save_viewer_poll_interval_secs=5)
        self.assertEqual(settings.save_viewer_poll_interval_secs, 5)

        # Boundary conditions
        settings = DisplaySettings(save_viewer_poll_interval_secs=1)
        self.assertEqual(settings.save_viewer_poll_interval_secs, 1)

        settings = DisplaySettings(save_viewer_poll_interval_secs=30)
        self.assertEqual(settings.save_viewer_poll_interval_secs, 30)

        # None disables polling
        settings = DisplaySettings(save_viewer_poll_interval_secs=None)
        self.assertIsNone(settings.save_viewer_poll_interval_secs)

        with self.assertRaises(ValidationError):
            DisplaySettings(save_viewer_poll_interval_secs=0)

        with self.assertRaises(ValidationError):
            DisplaySettings(save_viewer_poll_interval_secs=-1)

        with self.assertRaises(ValidationError):
            DisplaySettings(save_viewer_poll_interval_secs=31)

        with self.assertRaises(ValidationError):
            DisplaySettings(save_viewer_poll_interval_secs="notanumber")
