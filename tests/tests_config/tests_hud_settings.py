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
        self.assertEqual(settings.toggle_overlays_udp_action_code, 10)
        self.assertEqual(settings.show_lap_timer, True)
        self.assertEqual(settings.show_timing_tower, True)
        self.assertEqual(settings.show_mfd, True)
        self.assertEqual(settings.cycle_mfd_udp_action_code, 9)
        self.assertEqual(settings.overlays_opacity, 100)

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

    def test_udp_action_code_validation(self):
        """Test valid and invalid log_file_size values"""
        # Valid value
        action_code = 2
        hud_settings = HudSettings(toggle_overlays_udp_action_code=action_code)
        self.assertEqual(hud_settings.toggle_overlays_udp_action_code, action_code)

        with self.assertRaises(ValidationError):
            HudSettings(toggle_overlays_udp_action_code=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(toggle_overlays_udp_action_code="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(toggle_overlays_udp_action_code=420)

        # Boundary value: minimum (1)
        min_action_code = 1
        hud_settings_min = HudSettings(toggle_overlays_udp_action_code=min_action_code)
        self.assertEqual(hud_settings_min.toggle_overlays_udp_action_code, min_action_code)
        # Boundary value: maximum (12)
        max_action_code = 12
        hud_settings_max = HudSettings(toggle_overlays_udp_action_code=max_action_code)
        self.assertEqual(hud_settings_max.toggle_overlays_udp_action_code, max_action_code)
        with self.assertRaises(ValidationError):
            HudSettings(toggle_overlays_udp_action_code=None)  # type: ignore

    def test_show_lap_timer_validation(self):
        """Test valid and invalid show_lap_timer values"""
        # Valid value
        show_lap_timer = True
        hud_settings = HudSettings(show_lap_timer=show_lap_timer)
        self.assertEqual(hud_settings.show_lap_timer, show_lap_timer)

        with self.assertRaises(ValidationError):
            HudSettings(show_lap_timer=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(show_lap_timer="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(show_lap_timer=420)

    def test_show_timing_tower_validation(self):
        """Test valid and invalid show_timing_tower values"""
        # Valid value
        show_timing_tower = True
        hud_settings = HudSettings(show_timing_tower=show_timing_tower)
        self.assertEqual(hud_settings.show_timing_tower, show_timing_tower)

        with self.assertRaises(ValidationError):
            HudSettings(show_timing_tower=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(show_timing_tower="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(show_timing_tower=420)

    def test_overlays_opacity_validation(self):
        """Test valid and invalid overlays_opacity values"""
        # Valid value
        opacity = 75
        hud_settings = HudSettings(overlays_opacity=opacity)
        self.assertEqual(hud_settings.overlays_opacity, opacity)

        with self.assertRaises(ValidationError):
            HudSettings(overlays_opacity=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(overlays_opacity="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(overlays_opacity=-10)

        with self.assertRaises(ValidationError):
            HudSettings(overlays_opacity=150)

        # Boundary value: minimum (0)
        min_opacity = 0
        hud_settings_min = HudSettings(overlays_opacity=min_opacity)
        self.assertEqual(hud_settings_min.overlays_opacity, min_opacity)
        # Boundary value: maximum (100)
        max_opacity = 100
        hud_settings_max = HudSettings(overlays_opacity=max_opacity)
        self.assertEqual(hud_settings_max.overlays_opacity, max_opacity)
        with self.assertRaises(ValidationError):
            HudSettings(overlays_opacity=None)  # type: ignore

    def test_show_mfd_validation(self):
        """Test valid and invalid show_mfd values"""
        # Valid value
        show_mfd = True
        hud_settings = HudSettings(show_mfd=show_mfd)
        self.assertEqual(hud_settings.show_mfd, show_mfd)

        with self.assertRaises(ValidationError):
            HudSettings(show_mfd=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(show_mfd="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(show_mfd=420)

    def test_cycle_mfd_udp_action_code_validation(self):
        """Test valid and invalid cycle_mfd_udp_action_code values"""
        # Valid value
        action_code = 2
        hud_settings = HudSettings(cycle_mfd_udp_action_code=action_code)
        self.assertEqual(hud_settings.cycle_mfd_udp_action_code, action_code)

        with self.assertRaises(ValidationError):
            HudSettings(cycle_mfd_udp_action_code=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(cycle_mfd_udp_action_code="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(cycle_mfd_udp_action_code=420)

        # Boundary value: minimum (1)
        min_action_code = 1
        hud_settings_min = HudSettings(cycle_mfd_udp_action_code=min_action_code)
        self.assertEqual(hud_settings_min.cycle_mfd_udp_action_code, min_action_code)
        # Boundary value: maximum (12)
        max_action_code = 12
        hud_settings_max = HudSettings(cycle_mfd_udp_action_code=max_action_code)
        self.assertEqual(hud_settings_max.cycle_mfd_udp_action_code, max_action_code)
        with self.assertRaises(ValidationError):
            HudSettings(cycle_mfd_udp_action_code=None)  # type: ignore

        # Non-integer float value should raise ValidationError
        with self.assertRaises(ValidationError):
            HudSettings(cycle_mfd_udp_action_code=5.5)

    def test_hud_enabled_dependency(self):
        """Test hud_enabled dependency on show_lap_timer, show_timing_tower values, show_mfd"""

        # Disable all overlays and enable HUD
        with self.assertRaises(ValidationError):
            HudSettings(enabled=True, show_lap_timer=False, show_timing_tower=False, show_mfd=False)

        # Enable atleast one overlay
        settings = HudSettings(enabled=True, show_lap_timer=True, show_timing_tower=False, show_mfd=False)
        self.assertEqual(settings.enabled, True)
        self.assertEqual(settings.show_lap_timer, True)
        self.assertEqual(settings.show_timing_tower, False)
        self.assertEqual(settings.show_mfd, False)
