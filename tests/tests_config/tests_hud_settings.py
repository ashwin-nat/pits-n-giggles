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

from lib.config import (INPUT_TELEMETRY_OVERLAY_ID, LAP_TIMER_OVERLAY_ID,
                        MFD_OVERLAY_ID, TIMING_TOWER_OVERLAY_ID,
                        TRACK_RADAR_OVERLAY_ID, HudSettings, MfdPageSettings,
                        MfdSettings, OverlayPosition, TimingTowerColOptions,
                        WeatherMFDUIType)
from lib.config.schema.hud.mfd import DEFAULT_PAGES

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestHudSettings(TestF1ConfigBase):
    """Test LoggingSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = HudSettings()
        self.assertEqual(settings.enabled, False)
        self.assertEqual(settings.toggle_overlays_udp_action_code, None)
        self.assertEqual(settings.show_lap_timer, True)
        self.assertEqual(settings.lap_timer_ui_scale, 1.0)
        self.assertEqual(settings.show_timing_tower, True)
        self.assertEqual(settings.lap_timer_toggle_udp_action_code, None)
        self.assertEqual(settings.timing_tower_ui_scale, 1.0)
        self.assertEqual(settings.timing_tower_max_rows, 5)
        self.assertEqual(settings.timing_tower_toggle_udp_action_code, None)
        self.assertTrue(settings.timing_tower_col_options.show_deltas)
        self.assertTrue(settings.timing_tower_col_options.show_tyre_info)
        self.assertTrue(settings.timing_tower_col_options.show_team_logos)
        self.assertTrue(settings.timing_tower_col_options.show_ers_drs_info)
        self.assertTrue(settings.timing_tower_col_options.show_pens)
        self.assertTrue(settings.timing_tower_col_options.show_tl_warns)
        self.assertEqual(settings.show_mfd, True)
        self.assertEqual(settings.mfd_ui_scale, 1.0)
        self.assertEqual(settings.mfd_toggle_udp_action_code, None)
        self.assertEqual(settings.mfd_interaction_udp_action_code, None)
        self.assertEqual(settings.mfd_tyre_wear_threshold, 80)
        self.assertEqual(settings.mfd_weather_page_ui_type, WeatherMFDUIType.CARDS)
        self.assertEqual(settings.cycle_mfd_udp_action_code, None)
        self.assertEqual(settings.prev_mfd_page_udp_action_code, None)
        self.assertEqual(settings.show_track_map, False)
        self.assertEqual(settings.track_map_ui_scale, 1.0)
        self.assertEqual(settings.show_input_overlay, True)
        self.assertEqual(settings.input_overlay_ui_scale, 1.0)
        self.assertEqual(settings.input_overlay_toggle_udp_action_code, None)
        self.assertEqual(settings.input_overlay_buffer_duration_sec, 5.0)
        self.assertEqual(settings.show_track_radar_overlay, True)
        self.assertEqual(settings.track_radar_overlay_ui_scale, 1.0)
        self.assertEqual(settings.track_radar_overlay_toggle_udp_action_code, None)
        self.assertEqual(settings.track_radar_idle_opacity, 30)
        self.assertEqual(settings.overlays_opacity, 100)
        self.assertEqual(settings.use_windowed_overlays, False)
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
        """Ensure all UDP toggle fields validate correctly."""

        udp_action_code_fields = [
            "toggle_overlays_udp_action_code",
            "lap_timer_toggle_udp_action_code",
            "timing_tower_toggle_udp_action_code",
            "mfd_toggle_udp_action_code",
            "cycle_mfd_udp_action_code",
            "prev_mfd_page_udp_action_code",
            "track_map_toggle_udp_action_code",
            "input_overlay_toggle_udp_action_code",
            "mfd_interaction_udp_action_code",
        ]
        for field in udp_action_code_fields:
            with self.subTest(field=field):
                # 1. Valid integer
                settings = HudSettings(**{field: 2})
                self.assertEqual(getattr(settings, field), 2)

                # 2. Invalid string
                with self.assertRaises(ValidationError):
                    HudSettings(**{field: "invalid"})

                # 3. Invalid out-of-range
                with self.assertRaises(ValidationError):
                    HudSettings(**{field: 420})

                # 4. Boundary: min
                settings_min = HudSettings(**{field: 1})
                self.assertEqual(getattr(settings_min, field), 1)

                # 5. Boundary: max
                settings_max = HudSettings(**{field: 12})
                self.assertEqual(getattr(settings_max, field), 12)

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

    def test_timing_tower_max_rows_validation(self):
        """Test valid and invalid timing_tower_max_rows values"""
        # Valid value
        max_rows = 3
        hud_settings = HudSettings(timing_tower_max_rows=max_rows)
        self.assertEqual(hud_settings.timing_tower_max_rows, max_rows)
        self.assertEqual(hud_settings.timing_tower_num_adjacent_cars, 1)

        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_max_rows=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_max_rows="invalid")

        # Even number within acceptable range
        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_max_rows=16)

        # Odd number within acceptable range
        HudSettings(timing_tower_max_rows=17)

        # Well out of boundary
        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_max_rows=-10)
        with self.assertRaises(ValidationError):
            HudSettings(timing_tower_max_rows=420)

        # Boundary - valid
        hud_settings = HudSettings(timing_tower_max_rows=1)
        self.assertEqual(hud_settings.timing_tower_max_rows, 1)
        self.assertEqual(hud_settings.timing_tower_num_adjacent_cars, 0)

        hud_settings = HudSettings(timing_tower_max_rows=21)
        self.assertEqual(hud_settings.timing_tower_max_rows, 21)
        self.assertEqual(hud_settings.timing_tower_num_adjacent_cars, 10)

        hud_settings = HudSettings(timing_tower_max_rows=22)
        self.assertEqual(hud_settings.timing_tower_max_rows, 22)
        self.assertEqual(hud_settings.timing_tower_num_adjacent_cars, 11)

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

    def test_hud_enabled_dependency(self):
        """Test hud_enabled dependency on show_lap_timer, show_timing_tower values, show_mfd"""

        # Disable all overlays and enable HUD
        with self.assertRaises(ValidationError):
            HudSettings(enabled=True,
                        show_lap_timer=False,
                        show_timing_tower=False,
                        show_mfd=False,
                        show_track_map=False,
                        show_input_overlay=False,
                        show_track_radar_overlay=False)

        # Enable atleast one overlay
        settings = HudSettings(enabled=True, show_lap_timer=True, show_timing_tower=False,
                               show_mfd=False, show_track_map=False, show_input_overlay=False,
                               show_track_radar_overlay=False)
        self.assertEqual(settings.enabled, True)
        self.assertEqual(settings.show_lap_timer, True)
        self.assertEqual(settings.show_timing_tower, False)
        self.assertEqual(settings.show_mfd, False)
        self.assertEqual(settings.show_track_map, False)
        self.assertEqual(settings.show_input_overlay, False)
        self.assertEqual(settings.show_track_radar_overlay, False)

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
            "tyre_sets",
        }

        for page in expected_pages:
            self.assertIn(page, mfd.pages)
            self.assertIsInstance(mfd.pages[page], MfdPageSettings)

        for page in mfd.pages.keys():
            self.assertIn(page, expected_pages)

    def test_mfd_default_positions_unique(self):
        """All default enabled pages must have unique positions"""
        settings = HudSettings()
        mfd = settings.mfd_settings

        positions = [
            p.position for p in mfd.pages.values()
            if p.enabled
        ]

        self.assertEqual(len(positions), len(set(positions)))

    def test_model_validator_adds_missing_pages(self):
        data = {
            "pages": {
                "lap_times": {"enabled": True, "position": 1}
            }
        }

        mfd = MfdSettings.model_validate(data)

        for key in DEFAULT_PAGES:
            self.assertIn(key, mfd.pages)

        assert mfd.pages["tyre_sets"].enabled is False

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

    def test_use_windowed_overlays(self):
        windowed_overlays = True
        hud_settings = HudSettings(use_windowed_overlays=windowed_overlays)
        self.assertEqual(hud_settings.use_windowed_overlays, windowed_overlays)

        with self.assertRaises(ValidationError):
            HudSettings(use_windowed_overlays=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(use_windowed_overlays="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(use_windowed_overlays=420)

    def test_show_track_map(self):
        show_track_map = True
        hud_settings = HudSettings(show_track_map=show_track_map)
        self.assertEqual(hud_settings.show_track_map, show_track_map)

        with self.assertRaises(ValidationError):
            HudSettings(show_track_map=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(show_track_map="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(show_track_map=420)

    def test_track_map_ui_scale(self):
        track_map_ui_scale = 1.1
        hud_settings = HudSettings(track_map_ui_scale=track_map_ui_scale)
        self.assertEqual(hud_settings.track_map_ui_scale, track_map_ui_scale)

        with self.assertRaises(ValidationError):
            HudSettings(track_map_ui_scale=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(track_map_ui_scale="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(track_map_ui_scale=420)

        # Boundary value: minimum (0.5)
        with self.assertRaises(ValidationError):
            HudSettings(track_map_ui_scale=0.4)
        HudSettings(track_map_ui_scale=0.5)

        # Boundary value: maximum (2.0)
        with self.assertRaises(ValidationError):
            HudSettings(track_map_ui_scale=2.1)
        HudSettings(track_map_ui_scale=2.0)

    def test_show_input_overlay(self):
        show_input_overlay = True
        hud_settings = HudSettings(show_input_overlay=show_input_overlay)
        self.assertEqual(hud_settings.show_input_overlay, show_input_overlay)

        with self.assertRaises(ValidationError):
            HudSettings(show_input_overlay=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(show_input_overlay="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(show_input_overlay=420)

    def test_input_overlay_ui_scale(self):
        input_overlay_ui_scale = 1.1
        hud_settings = HudSettings(input_overlay_ui_scale=input_overlay_ui_scale)
        self.assertEqual(hud_settings.input_overlay_ui_scale, input_overlay_ui_scale)

        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_ui_scale=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_ui_scale="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_ui_scale=420)

        # Boundary value: minimum (0.5)
        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_ui_scale=0.4)
        HudSettings(input_overlay_ui_scale=0.5)

        # Boundary value: maximum (2.0)
        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_ui_scale=2.1)
        HudSettings(input_overlay_ui_scale=2.0)

    def test_input_overlay_buffer_duration_sec(self):
        input_overlay_buffer_duration_sec = 1.1
        hud_settings = HudSettings(input_overlay_buffer_duration_sec=input_overlay_buffer_duration_sec)
        self.assertEqual(hud_settings.input_overlay_buffer_duration_sec, input_overlay_buffer_duration_sec)

        # int should be accepted
        HudSettings(input_overlay_buffer_duration_sec=2)

        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_buffer_duration_sec=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_buffer_duration_sec="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_buffer_duration_sec=420)

        # Boundary conditions
        HudSettings(input_overlay_buffer_duration_sec=1.0)
        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_buffer_duration_sec=0.9)

        HudSettings(input_overlay_buffer_duration_sec=20.0)
        with self.assertRaises(ValidationError):
            HudSettings(input_overlay_buffer_duration_sec=21.0)

    def test_show_track_radar(self):
        show_track_radar_overlay = True
        hud_settings = HudSettings(show_track_radar_overlay=show_track_radar_overlay)
        self.assertEqual(hud_settings.show_track_radar_overlay, show_track_radar_overlay)

        with self.assertRaises(ValidationError):
            HudSettings(show_track_radar_overlay=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(show_track_radar_overlay="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(show_track_radar_overlay=420)

    def test_track_radar_overlay_ui_scale(self):
        track_radar_overlay_ui_scale = 1.1
        hud_settings = HudSettings(track_radar_overlay_ui_scale=track_radar_overlay_ui_scale)
        self.assertEqual(hud_settings.track_radar_overlay_ui_scale, track_radar_overlay_ui_scale)

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_ui_scale=None)  # type: ignore

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_ui_scale="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_ui_scale=420)

        # Boundary value: minimum (0.5)
        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_ui_scale=0.4)
        HudSettings(track_radar_overlay_ui_scale=0.5)

        # Boundary value: maximum (2.0)
        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_ui_scale=2.1)
        HudSettings(track_radar_overlay_ui_scale=2.0)

    def test_track_radar_overlay_toggle_udp_action_code(self):
        track_radar_overlay_toggle_udp_action_code = 1
        hud_settings = HudSettings(track_radar_overlay_toggle_udp_action_code=track_radar_overlay_toggle_udp_action_code)
        self.assertEqual(hud_settings.track_radar_overlay_toggle_udp_action_code, track_radar_overlay_toggle_udp_action_code)

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_toggle_udp_action_code="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_overlay_toggle_udp_action_code=420)

    def test_new_key_in_layout_defaults(self):

        # Assume input_telemetry is new
        loaded_settings = HudSettings(enabled=True,
                                      layout={
                                          LAP_TIMER_OVERLAY_ID: OverlayPosition(x=1, y=1),
                                          TIMING_TOWER_OVERLAY_ID: OverlayPosition(x=2, y=2),
                                          MFD_OVERLAY_ID: OverlayPosition(x=3, y=3),
                                          TRACK_RADAR_OVERLAY_ID: OverlayPosition(x=4, y=4),
                                      })

        # Validate that the input telemetry key got inserted with defaults
        self.assertIn(INPUT_TELEMETRY_OVERLAY_ID, loaded_settings.layout)
        self.assertEqual(loaded_settings.layout[INPUT_TELEMETRY_OVERLAY_ID],
                         HudSettings.get_default_layout_dict()[INPUT_TELEMETRY_OVERLAY_ID])

        # Validate that the other keys are still there and their values are preserved
        self.assertIn(LAP_TIMER_OVERLAY_ID, loaded_settings.layout)
        self.assertEqual(loaded_settings.layout[LAP_TIMER_OVERLAY_ID], OverlayPosition(x=1, y=1))
        self.assertIn(TIMING_TOWER_OVERLAY_ID, loaded_settings.layout)
        self.assertEqual(loaded_settings.layout[TIMING_TOWER_OVERLAY_ID], OverlayPosition(x=2, y=2))
        self.assertIn(MFD_OVERLAY_ID, loaded_settings.layout)
        self.assertEqual(loaded_settings.layout[MFD_OVERLAY_ID], OverlayPosition(x=3, y=3))
        self.assertIn(TRACK_RADAR_OVERLAY_ID, loaded_settings.layout)
        self.assertEqual(loaded_settings.layout[TRACK_RADAR_OVERLAY_ID], OverlayPosition(x=4, y=4))

    def test_col_options_diff(self):

        # Diff from parent obj - no diff
        old_settings = HudSettings()
        new_settings = HudSettings()
        self.assertFalse(old_settings.has_changed(new_settings))
        self.assertEqual(old_settings.diff(new_settings), {})

        # Diff from parent obj - real diff
        new_settings = HudSettings(
            timing_tower_col_options=TimingTowerColOptions(
                show_ers_drs_info=False,
            )
        )
        self.assertTrue(old_settings.has_changed(new_settings))
        self.assertEqual(old_settings.diff(new_settings), {
            "timing_tower_col_options": {
                "show_ers_drs_info": {
                    "old_value": True,
                    "new_value": False
                }
            }
        })

        # Diff from obj directly - no diff
        old_settings = TimingTowerColOptions()
        new_settings = TimingTowerColOptions()
        self.assertFalse(old_settings.has_changed(new_settings))
        self.assertEqual(old_settings.diff(new_settings), {})

        # Real diff
        new_settings = TimingTowerColOptions(
            show_ers_drs_info=False,
        )
        self.assertTrue(old_settings.has_changed(new_settings))
        self.assertEqual(old_settings.diff(new_settings), {
            "show_ers_drs_info": {
                "old_value": True,
                "new_value": False
            }
        })

    def test_idle_opacity(self):

        idle_opacity = 50
        hud_settings = HudSettings(track_radar_idle_opacity=idle_opacity)
        self.assertEqual(hud_settings.track_radar_idle_opacity, idle_opacity)

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_idle_opacity="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_idle_opacity=420)

        with self.assertRaises(ValidationError):
            HudSettings(track_radar_idle_opacity=None)

        # Boundary value: minimum (0)
        with self.assertRaises(ValidationError):
            HudSettings(track_radar_idle_opacity=-1)
        HudSettings(track_radar_idle_opacity=0)

        # Boundary value: maximum (100)
        with self.assertRaises(ValidationError):
            HudSettings(track_radar_idle_opacity=101)
        HudSettings(track_radar_idle_opacity=100)

        # Idle opacity more than overall opacity
        with self.assertRaises(ValidationError):
            HudSettings(enabled=True, overlays_opacity=70, track_radar_idle_opacity=80)

    def test_mfd_tyre_wear_threshold(self):

        mfd_tyre_wear_threshold = 50
        hud_settings = HudSettings(mfd_tyre_wear_threshold=mfd_tyre_wear_threshold)
        self.assertEqual(hud_settings.mfd_tyre_wear_threshold, mfd_tyre_wear_threshold)

        with self.assertRaises(ValidationError):
            HudSettings(mfd_tyre_wear_threshold="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(mfd_tyre_wear_threshold=420)

        with self.assertRaises(ValidationError):
            HudSettings(mfd_tyre_wear_threshold=None)

        # Boundary value: minimum (0)
        with self.assertRaises(ValidationError):
            HudSettings(mfd_tyre_wear_threshold=-1)
        HudSettings(mfd_tyre_wear_threshold=0)

        # Boundary value: maximum (100)
        with self.assertRaises(ValidationError):
            HudSettings(mfd_tyre_wear_threshold=101)
        HudSettings(mfd_tyre_wear_threshold=100)

    def test_mfd_weather_page_ui_type(self):

        ui_type = WeatherMFDUIType.CARDS
        hud_settings = HudSettings(mfd_weather_page_ui_type=ui_type)
        self.assertEqual(hud_settings.mfd_weather_page_ui_type, ui_type)

        with self.assertRaises(ValidationError):
            HudSettings(mfd_weather_page_ui_type="invalid")

        with self.assertRaises(ValidationError):
            HudSettings(mfd_weather_page_ui_type=None)

        with self.assertRaises(ValidationError):
            HudSettings(mfd_weather_page_ui_type=420)

        with self.assertRaises(AttributeError):
            HudSettings(mfd_weather_page_ui_type=WeatherMFDUIType.UNKNOWN)
