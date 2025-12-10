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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
import logging
import os
from typing import Dict, Optional, Any

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QApplication

from apps.hud.ui.overlays import (LapTimerOverlay, MfdOverlay, InputTelemetryOverlay,
                                  TimingTowerOverlay)
from lib.assets_loader import load_fonts
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import PngSettings
from lib.file_path import resolve_user_file

from .config import OverlaysConfig
from .high_freq_types import InputTelemetryData
from .window_mgr import WindowManager

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_DEFAULT_OVERLAYS_CONFIG: Dict[str, OverlaysConfig] = {
    LapTimerOverlay.OVERLAY_ID: OverlaysConfig(
        x=600,
        y=60,
    ),
    TimingTowerOverlay.OVERLAY_ID: OverlaysConfig(
        x=10,
        y=55,
    ),
    MfdOverlay.OVERLAY_ID: OverlaysConfig(
        x=10,
        y=355,
    ),
    # TrackMapOverlay.OVERLAY_ID: OverlaysConfig(
    #     x=10,
    #     y=600,
    # ),
    InputTelemetryOverlay.OVERLAY_ID: OverlaysConfig(
        x=10,
        y=600,
    ),
}

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class OverlaysMgr:
    def __init__(self,
                 logger: logging.Logger,
                 settings: PngSettings,
                 config_file: Optional[str] = 'png_overlays.json',
                 debug: bool = False):
        """Construct a new OverlaysMgr object. Ctor will init config files and windows

        Args:
            logger (logging.Logger): Logger object
            settings (PngSettings): App Settings
            config_file (str, optional): Path to config file. Defaults to 'png_overlays.json'.
            debug (bool, optional): Debug mode. Defaults to False.
        """
        self.app = QApplication()
        self.logger = logger
        load_fonts(debug_log_printer=self.logger.debug, error_log_printer=self.logger.error)
        self.config_file = resolve_user_file(config_file)
        self.debug_mode = debug
        self._init_config()
        self.running = False

        assert settings.HUD.enabled, "HUD must be enabled to run overlays manager"
        self.window_manager = WindowManager(logger, notify_parent_init_complete)

        if settings.HUD.show_lap_timer:
            self.window_manager.register_overlay(LapTimerOverlay.OVERLAY_ID, LapTimerOverlay(
                self.config[LapTimerOverlay.OVERLAY_ID],
                self.logger,
                locked=True,
                opacity=settings.HUD.overlays_opacity,
                scale_factor=settings.HUD.lap_timer_ui_scale,
                windowed_overlay=settings.HUD.use_windowed_overlays
            ))
        else:
            self.logger.debug("Lap timer overlay is disabled")

        if settings.HUD.show_timing_tower:
            self.window_manager.register_overlay(TimingTowerOverlay.OVERLAY_ID, TimingTowerOverlay(
                self.config[TimingTowerOverlay.OVERLAY_ID],
                self.logger,
                locked=True,
                opacity=settings.HUD.overlays_opacity,
                scale_factor=settings.HUD.timing_tower_ui_scale,
                num_adjacent_cars=settings.HUD.timing_tower_num_adjacent_cars,
                windowed_overlay=settings.HUD.use_windowed_overlays
            ))
        else:
            self.logger.debug("Timing tower overlay is disabled")

        if settings.HUD.show_mfd:
            self.window_manager.register_overlay(MfdOverlay.OVERLAY_ID, MfdOverlay(
                self.config[MfdOverlay.OVERLAY_ID],
                settings,
                self.logger,
                locked=True,
                opacity=settings.HUD.overlays_opacity,
                scale_factor=settings.HUD.mfd_ui_scale,
                windowed_overlay=settings.HUD.use_windowed_overlays
            ))
        else:
            self.logger.debug("MFD overlay is disabled")

        # if settings.HUD.show_track_map:
        #     self.window_manager.register_overlay(TrackMapOverlay.OVERLAY_ID, TrackMapOverlay(
        #         self.config[TrackMapOverlay.OVERLAY_ID],
        #         self.logger,
        #         locked=True,
        #         opacity=settings.HUD.overlays_opacity,
        #         scale_factor=settings.HUD.track_map_ui_scale,
        #         windowed_overlay=settings.HUD.use_windowed_overlays
        #     ))
        # else:
        #     self.logger.debug("Track map overlay is disabled")

        if settings.HUD.show_input_overlay:
            self.window_manager.register_overlay(InputTelemetryOverlay.OVERLAY_ID, InputTelemetryOverlay(
                self.config[InputTelemetryOverlay.OVERLAY_ID],
                self.logger,
                locked=True,
                opacity=settings.HUD.overlays_opacity,
                scale_factor=settings.HUD.input_overlay_ui_scale,
                windowed_overlay=settings.HUD.use_windowed_overlays
            ))
        else:
            self.logger.debug("Input telemetry overlay is disabled")

        self.logger.debug("Overlays manager initialized")

    def run(self):
        """Start the overlays manager"""
        self.running = True
        self.app.exec()

    def on_locked_state_change(self, args: Dict[str, bool]):
        """Handle locked state change"""
        self.window_manager.broadcast_data('set_locked_state', args)
        locked_value = args.get('new-value')
        if not locked_value:
            return

        changed = False
        for overlay_id in list(self.window_manager.overlays.keys()):
            curr_params = self._get_window_info(overlay_id)
            self.logger.debug(f"Current config for overlay '{overlay_id}' is {curr_params}")
            saved_params = self.config[overlay_id]
            if curr_params != saved_params:
                self.logger.debug(f"Updating config for overlay '{overlay_id}' to {curr_params}")
                self.config[overlay_id] = curr_params
                changed = True

        if changed:
            self._save_config()

    def race_table_update(self, data):
        """Handle race table update"""
        self.window_manager.broadcast_data('race_table_update', data)

    def toggle_overlays_visibility(self, oid: Optional[str] = ''):
        """Toggle overlays visibility"""

        self.logger.debug("Toggling overlays visibility. oid=%s", oid)
        if oid:
            self.window_manager.unicast_data(oid, 'toggle_visibility', {})
        else:
            self.window_manager.broadcast_data('toggle_visibility', {})

    def set_overlays_opacity(self, opacity: int):
        """Set overlays opacity"""
        self.logger.debug(f"Setting overlays opacity to {opacity}%")
        self.window_manager.broadcast_data('set_opacity', {'opacity': opacity})

    def next_page(self):
        """Go to the next page in MFD overlay"""
        self.window_manager.unicast_data(MfdOverlay.OVERLAY_ID, 'next_page', {})

    def reset_overlays(self):
        """Reset overlays"""
        self._reset_config()
        self.window_manager.set_config(self.config)

    def stream_overlays_update(self, data):
        """Handle the stream overlay update event"""
        self.window_manager.unicast_data(MfdOverlay.OVERLAY_ID , 'stream_overlay_update', data)

    def set_scale_factor(self, oid: str, scale_factor: float):
        """Set overlays scale factor to specified overlay"""

        self.logger.debug(f"Setting overlay {oid} scale factor to {scale_factor}")
        self.window_manager.unicast_data(oid, 'set_scale_factor', {'scale_factor': scale_factor})

    def stop(self):
        """Stop the overlays manager"""
        self.running = False
        QMetaObject.invokeMethod(
            self.app,
            "quit",
            Qt.ConnectionType.QueuedConnection
        )

    def _get_html_path_for_window(self, overlay_id: str) -> str:
        """Constructs the absolute path to the HTML file for a given window ID."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_file_path = os.path.join(base_dir, "..", "overlays", overlay_id, f"{overlay_id}.html")
        return html_file_path

    def _init_config(self):
        """"Load config file if it exists. Else, use default config."""
        should_write = False
        config = self._load_config()
        if not config:
            self.config = _DEFAULT_OVERLAYS_CONFIG
            self.logger.debug("Using default config")
            should_write = True
        else:
            # Check if any keys are missing from default config and add them with default values
            for key, value in _DEFAULT_OVERLAYS_CONFIG.items():
                if key not in config:
                    config[key] = value
                    self.logger.debug(f"Missing overlay config key. Added {key} to config")
                    should_write = True

            self.config = config
            json_str = json.dumps({k: v.toJSON() for k, v in self.config.items()}, indent=2)
            self.logger.debug(f"Final loaded config: \n{json_str}")
        if should_write:
            pass

    def _reset_config(self):
        """"Reset config to default"""
        self.config = _DEFAULT_OVERLAYS_CONFIG
        self._save_config()

    def _save_config(self):
        """"Save config file"""
        json_str = json.dumps({k: v.toJSON() for k, v in self.config.items()}, indent=2)
        self.logger.debug(f"Saving config to {self.config_file}. Config: \n{json_str}")
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.toJSON() for k, v in self.config.items()}, f, indent=4)

    def _load_config(self) -> Optional[Dict[str, OverlaysConfig]]:
        """"Load config file if it exists. Else, return None"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    try:
                        parsed_contents = json.load(f)
                        return {
                            overlay_id: OverlaysConfig.fromJSON(params)
                            for overlay_id, params in parsed_contents.items()
                        }
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self.logger.error(f"Failed to load config file: {e}. Falling back to default config")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.error(f"Failed to load config file: {e}. Falling back to default config")

        return None

    def _get_window_info(self, overlay_id: str, timeout_ms: int = 5000) -> Optional[OverlaysConfig]:
        """Thread-safe query for specific window info."""
        self.logger.debug(f"Requesting window info for {overlay_id}")
        ret = self.window_manager.request(overlay_id, "get_window_info", timeout_ms=timeout_ms)
        if not ret:
            return None
        return OverlaysConfig.fromJSON(ret)

    def input_telemetry_update(self, data: Dict[str, Any]):
        """Send input telemetry data to input telemetry overlay."""
        car_telemetry = data["car-telemetry"]
        self.window_manager.unicast_high_freq_data(
            InputTelemetryOverlay.OVERLAY_ID,
            InputTelemetryData(
                throttle=car_telemetry["throttle"],
                brake=car_telemetry["brake"],
                steering=car_telemetry["steering"]
            )
        )
