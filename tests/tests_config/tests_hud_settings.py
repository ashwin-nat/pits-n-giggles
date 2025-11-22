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

from lib.config import HudSettings, MfdSettings, MfdPageSettings

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
        self.assertEqual(settings.lap_timer_ui_scale, 1.0)
        self.assertEqual(settings.show_timing_tower, True)
        self.assertEqual(settings.timing_tower_ui_scale, 1.0)
        self.assertEqual(settings.show_mfd, True)
        self.assertEqual(settings.mfd_ui_scale, 1.0)
        self.assertEqual(settings.cycle_mfd_udp_action_code, 9)
        self.assertEqual(settings.overlays_opacity, 100)
        # MFD pages has its own test case because the structure is a bit more complex

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

    def test_lap_timer_ui_scale_validation(self):
        """Test valid and invalid lap_timer_ui_scale values"""
        # Valid value
        lap_timer_ui_scale = 1.5
        hud_settings = HudSettings(lap_timer_ui_scale=lap_timer_ui_scale)
        self.assertEqual(hud_settings.lap_timer_ui_scale, lap_timer_ui_scale)

        with self.assertRaises(ValidationError):
            HudSettings(lap_timer_ui_scale=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(lap_timer_ui_scale="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(lap_timer_ui_scale=420)

        # Boundary value: minimum (0.5)
        with self.assertRaises(ValidationError):
            HudSettings(lap_timer_ui_scale=0.4)
        HudSettings(lap_timer_ui_scale=0.5)

        # Boundary value: maximum (2.0)
        with self.assertRaises(ValidationError):
            HudSettings(lap_timer_ui_scale=2.1)
        HudSettings(lap_timer_ui_scale=2.0)

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

    def test_timing_tower_ui_scale_validation(self):
        """Test valid and invalid timing_tower_ui_scale values"""
        # Valid value
        timing_tower_ui_scale = 1.5
        hud_settings = HudSettings(timing_tower_ui_scale=timing_tower_ui_scale)
        self.assertEqual(hud_settings.timing_tower_ui_scale, timing_tower_ui_scale)

        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_ui_scale=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_ui_scale="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_ui_scale=420)

        # Boundary value: minimum (0.5)
        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_ui_scale=0.4)
        HudSettings(timing_tower_ui_scale=0.5)

        # Boundary value: maximum (2.0)
        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_ui_scale=2.1)
        HudSettings(timing_tower_ui_scale=2.0)

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

    def test_mfd_ui_scale_validation(self):
        """Test valid and invalid mfd_ui_scale values"""
        # Valid value
        mfd_ui_scale = 1.5
        hud_settings = HudSettings(mfd_ui_scale=mfd_ui_scale)
        self.assertEqual(hud_settings.mfd_ui_scale, mfd_ui_scale)

        with self.assertRaises(ValidationError):
            HudSettings(mfd_ui_scale=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(mfd_ui_scale="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(mfd_ui_scale=420)

        # Boundary value: minimum (0.5)
        with self.assertRaises(ValidationError):
            HudSettings(mfd_ui_scale=0.4)
        HudSettings(mfd_ui_scale=0.5)

        # Boundary value: maximum (2.0)
        with self.assertRaises(ValidationError):
            HudSettings(mfd_ui_scale=2.1)
        HudSettings(mfd_ui_scale=2.0)

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

    def test_mfd_default_pages(self):
        """Verify default MFD pages exist and are valid"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        self.assertIsInstance(mfd, MfdSettings)
        self.assertTrue(len(mfd.pages) > 0)

        expected_pages = {
            "lap_times",
            "weather_forecast",
            "fuel_info",
            "tyre_info",
            "pit_rejoin",
        }

        for page in expected_pages:
            self.assertIn(page, mfd.pages)
            self.assertIsInstance(mfd.pages[page], MfdPageSettings)

    def test_mfd_default_positions_unique(self):
        """All default enabled pages must have unique positions"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        positions = [
            p.position for p in mfd.pages.values()
            if p.enabled
        ]

        self.assertEqual(len(positions), len(set(positions)))

    #
    # ------------------------------------------------------------
    #  VALIDATION — DUPLICATE POSITIONS
    # ------------------------------------------------------------
    #

    def test_mfd_duplicate_positions_validation(self):
        """Duplicate enabled positions should raise ValidationError"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        # Force two pages to same position
        keys = list(mfd.pages.keys())
        mfd.pages[keys[0]].position = 0
        mfd.pages[keys[1]].position = 0

        with self.assertRaises(ValidationError):
            HudSettings(mfd_settings=mfd)

    #
    # ------------------------------------------------------------
    #  VALIDATION — MFD enabled and page disabled
    # ------------------------------------------------------------
    #

    def test_mfd_enabled_with_pages_disabled(self):
        """MFD cannot be enabled while all MFD pages are disabled"""
        with self.assertRaises(ValidationError):
            HudSettings(show_mfd=True,
                        mfd_settings={
                            {"lap_times": MfdPageSettings(enabled=False)},
                            {"fuel_info": MfdPageSettings(enabled=False)},
                            {"tyre_info": MfdPageSettings(enabled=False)},
                        }
            )


    #
    # ------------------------------------------------------------
    #  SORTING
    # ------------------------------------------------------------
    #

    def test_mfd_sorted_enabled_pages(self):
        """sorted_enabled_pages must return pages ordered by position"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        mfd.pages["lap_times"].position = 3
        mfd.pages["fuel_info"].position = 1
        mfd.pages["tyre_info"].position = 2

        sorted_pages = mfd.sorted_enabled_pages()

        positions = [p.position for _, p in sorted_pages]
        self.assertEqual(positions, sorted(positions))

    def test_mfd_sorted_excludes_disabled(self):
        """Disabled pages must be excluded from sorted output"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        mfd.pages["lap_times"].enabled = False
        mfd.pages["fuel_info"].enabled = True

        sorted_pages = mfd.sorted_enabled_pages()

        self.assertNotIn("lap_times", [name for name, _ in sorted_pages])
        self.assertIn("fuel_info", [name for name, _ in sorted_pages])

    #
    # ------------------------------------------------------------
    #  ADDING / REMOVING PAGES
    # ------------------------------------------------------------
    #

    def test_mfd_add_page(self):
        """Adding a new MFD page should be allowed and valid"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        mfd.pages["new_page"] = MfdPageSettings(enabled=True, position=25)

        self.assertIn("new_page", mfd.pages)
        self.assertEqual(mfd.pages["new_page"].position, 25)

    #
    # ------------------------------------------------------------
    #  DIFF BEHAVIOR
    # ------------------------------------------------------------
    #

    def test_mfd_diff_internal_field_change(self):
        """Changing a field inside a page must show up in the diff"""
        old = HudSettings()
        new = HudSettings()

        new.mfd_settings.pages["lap_times"].position = 50

        diff = new.diff(old)

        self.assertIn("mfd_settings", diff)
        self.assertIn("pages", diff["mfd_settings"])
        self.assertIn("lap_times", diff["mfd_settings"]["pages"])
        self.assertIn("position", diff["mfd_settings"]["pages"]["lap_times"])

        self.assertEqual(
            diff["mfd_settings"]["pages"]["lap_times"]["position"]["old_value"],
            50
        )
        self.assertEqual(
            diff["mfd_settings"]["pages"]["lap_times"]["position"]["new_value"],
            old.mfd_settings.pages["lap_times"].position
        )

    #
    # ------------------------------------------------------------
    #  ENABLE / DISABLE PAGE
    # ------------------------------------------------------------
    #

    def test_mfd_enable_disable_page_affects_diff(self):
        old = HudSettings()
        new = HudSettings()

        new.mfd_settings.pages["tyre_info"].enabled = False

        diff = new.diff(old)

        self.assertIn("mfd_settings", diff)
        self.assertIn("pages", diff["mfd_settings"])
        self.assertIn("tyre_info", diff["mfd_settings"]["pages"])
        self.assertIn("enabled", diff["mfd_settings"]["pages"]["tyre_info"])
