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

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QApplication

from apps.hud.ui.overlays import (BaseOverlay, InputTelemetryOverlay,
                                  LapTimerOverlay, MfdOverlay,
                                  TimingTowerOverlay, TrackRadarOverlay)
from lib.assets_loader import load_fonts
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import OverlayPosition, PngSettings
from lib.rate_limiter import RateLimiter

from .hf_types import InputTelemetryData, LiveSessionMotionInfo
from .window_mgr import WindowManager

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class OverlaysMgr:
    def __init__(self,
                 logger: logging.Logger,
                 settings: PngSettings,
                 debug: bool = False):
        """Construct a new OverlaysMgr object. Ctor will init config files and windows

        Args:
            logger (logging.Logger): Logger object
            settings (PngSettings): App Settings
            debug (bool, optional): Debug mode. Defaults to False.
        """
        self.app = QApplication()
        self.logger = logger
        load_fonts(debug_log_printer=self.logger.debug, error_log_printer=self.logger.error)
        self.debug_mode = debug
        self.running = False
        self.rate_limiter = RateLimiter(interval_ms=settings.Display.refresh_interval)

        assert settings.HUD.enabled, "HUD must be enabled to run overlays manager"
        self.window_manager = WindowManager(logger, notify_parent_init_complete)

        self._register_overlay_if_enabled(
            enabled=settings.HUD.show_lap_timer,
            overlay_cls=LapTimerOverlay,
            overlay_cfg=settings.HUD.layout[LapTimerOverlay.OVERLAY_ID],
            opacity=settings.HUD.overlays_opacity,
            windowed_overlay=settings.HUD.use_windowed_overlays,
            scale_factor=settings.HUD.lap_timer_ui_scale,
        )

        self._register_overlay_if_enabled(
            enabled=settings.HUD.show_timing_tower,
            overlay_cls=TimingTowerOverlay,
            opacity=settings.HUD.overlays_opacity,
            overlay_cfg=settings.HUD.layout[TimingTowerOverlay.OVERLAY_ID],
            windowed_overlay=settings.HUD.use_windowed_overlays,
            scale_factor=settings.HUD.timing_tower_ui_scale,
            num_adjacent_cars=settings.HUD.timing_tower_num_adjacent_cars,
        )

        self._register_overlay_if_enabled(
            enabled=settings.HUD.show_input_overlay,
            overlay_cls=InputTelemetryOverlay,
            opacity=settings.HUD.overlays_opacity,
            overlay_cfg=settings.HUD.layout[InputTelemetryOverlay.OVERLAY_ID],
            windowed_overlay=settings.HUD.use_windowed_overlays,
            scale_factor=settings.HUD.input_overlay_ui_scale,
            refresh_interval_ms=settings.Display.realtime_overlay_update_interval_ms,
            window_duration_sec=settings.HUD.input_overlay_buffer_duration_sec
        )


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

        self._register_overlay_if_enabled(
            enabled=settings.HUD.show_track_radar_overlay,
            overlay_cls=TrackRadarOverlay,
            opacity=settings.HUD.overlays_opacity,
            overlay_cfg=settings.HUD.layout[TrackRadarOverlay.OVERLAY_ID],
            windowed_overlay=settings.HUD.use_windowed_overlays,
            scale_factor=settings.HUD.track_radar_overlay_ui_scale,
            refresh_interval_ms=settings.Display.realtime_overlay_update_interval_ms
        )

        if settings.HUD.show_mfd:
            self.window_manager.register_overlay(
                MfdOverlay.OVERLAY_ID,
                MfdOverlay(
                    settings.HUD.layout[MfdOverlay.OVERLAY_ID],
                    settings,
                    self.logger,
                    locked=True,
                    opacity=settings.HUD.overlays_opacity,
                    scale_factor=settings.HUD.mfd_ui_scale,
                    windowed_overlay=settings.HUD.use_windowed_overlays
                )
            )
        else:
            self.logger.debug("MFD overlay is disabled")

        self.logger.debug("Overlays manager initialized")

    def run(self):
        """Start the overlays manager"""
        self.running = True
        self.app.exec()

    def stop(self):
        """Stop the overlays manager"""
        self.running = False
        QMetaObject.invokeMethod(
            self.app,
            "quit",
            Qt.ConnectionType.QueuedConnection
        )

    # -------------------------------------- DATA HANDLERS -------------------------------------------------------------

    def race_table_update(self, data):
        """Handle race table update"""
        self.window_manager.broadcast_data('race_table_update', data)

    def stream_overlays_update(self, data):
        """Handle the stream overlay update event"""
        self._input_telemetry_update(data)
        self._motion_update(data)
        if self.rate_limiter.allows("stream-overlay-update"):
            self.window_manager.unicast_data(MfdOverlay.OVERLAY_ID , 'stream_overlay_update', data)

    # -------------------------------------- CONTROL HANDLERS ----------------------------------------------------------

    def toggle_overlays_visibility(self, oid: Optional[str] = ''):
        """Toggle overlays visibility"""

        self.logger.debug("Toggling overlays visibility. oid=%s", oid)
        if oid:
            self.window_manager.unicast_data(oid, '__toggle_visibility__', {})
        else:
            self.window_manager.broadcast_data('__toggle_visibility__', {})

    def on_locked_state_change(self, args: Dict[str, bool]):
        """Handle locked state change."""
        rsp = {
            "status": "success",
            "message": "lock-widgets handler executed.",
        }

        # --------------------------------------------------
        # 1. Validate input
        # --------------------------------------------------
        locked_value = args.get("new-value")
        if not isinstance(locked_value, bool):
            rsp["status"] = "error"
            rsp["message"] = "Invalid or missing 'new-value' in args"
            return rsp

        # --------------------------------------------------
        # 2. Broadcast locked state
        # --------------------------------------------------
        try:
            self.window_manager.broadcast_data("__set_locked_state__", args)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception("Failed to broadcast locked state")
            rsp["status"] = "error"
            rsp["message"] = "Failed to apply locked state to overlays"
            rsp["error"] = str(e)
            return rsp

        # If unlocking, nothing to persist
        if not locked_value:
            return rsp

        # --------------------------------------------------
        # 3. Capture layout (transactional)
        # --------------------------------------------------
        layout = {}

        for overlay_id in list(self.window_manager.overlays.keys()):
            try:
                curr_params = self._get_window_info(overlay_id)
                self.logger.debug(
                    "Current config for overlay '%s' is %s",
                    overlay_id,
                    curr_params,
                )
                layout[overlay_id] = curr_params.toJSON()

            except Exception as e:  # pylint: disable=broad-except
                self.logger.exception(
                    "Aborting layout capture; failed for overlay '%s'",
                    overlay_id,
                )
                rsp["status"] = "error"
                rsp["message"] = "Failed to capture overlay layout"
                rsp["error"] = f"{overlay_id}: {e}"
                return rsp

        # --------------------------------------------------
        # 4. Finalise response
        # --------------------------------------------------
        rsp["layout"] = layout
        return rsp

    def set_overlays_opacity(self, opacity: int):
        """Set overlays opacity"""
        self.logger.debug(f"Setting overlays opacity to {opacity}%")
        self.window_manager.broadcast_data('__set_opacity__', {'opacity': opacity})

    def next_page(self):
        """Go to the next page in MFD overlay"""
        self.window_manager.unicast_data(MfdOverlay.OVERLAY_ID, 'next_page', {})

    def set_overlays_layout(self, layout: Dict[str, Dict[str, int]]):
        """Apply a full overlays layout snapshot."""
        rsp = {
            "status": "success",
            "message": "Overlays layout applied successfully.",
        }

        if not isinstance(layout, dict):
            rsp["status"] = "error"
            rsp["error"] = "Invalid layout payload (expected dict)"
            return rsp

        for overlay_id, overlay_layout in layout.items():
            try:
                self.window_manager.unicast_data(
                    overlay_id,
                    "__set_config__",
                    overlay_layout,
                )
            except Exception as e:  # pylint: disable=broad-except
                self.logger.exception(
                    "Failed to apply layout for overlay '%s'",
                    overlay_id,
                )
                rsp["status"] = "error"
                rsp["error"] = f"{overlay_id}: {e}"
                return rsp

        # Enable all overlays so that the user can see the new layout
        self._set_overlays_visibility(True)
        return rsp

    def set_scale_factor(self, oid: str, scale_factor: float):
        """Set overlays scale factor to specified overlay"""

        self.logger.debug(f"Setting overlay {oid} scale factor to {scale_factor}")
        self.window_manager.unicast_data(oid, '__set_scale_factor__', {'scale_factor': scale_factor})

    # -------------------------------------- HELPERS -------------------------------------------------------------------

    def _reset_config(self):
        """"Reset config to default"""
        pass # TODO

    def _get_window_info(self, overlay_id: str, timeout_ms: int = 5000) -> Optional[OverlayPosition]:
        """Thread-safe query for specific window info."""
        self.logger.debug(f"Requesting window info for {overlay_id}")
        ret = self.window_manager.request(overlay_id, "get_window_info", timeout_ms=timeout_ms)
        if not ret:
            return None
        return OverlayPosition.fromJSON(ret)

    def _register_overlay_if_enabled(
        self,
        *,
        enabled: bool,
        overlay_cls: BaseOverlay,
        overlay_cfg: OverlayPosition,
        opacity: float,
        windowed_overlay: bool,
        **overlay_kwargs
    ):
        if not enabled:
            self.logger.debug(f"{overlay_cls.OVERLAY_ID} overlay is disabled")
            return

        self.window_manager.register_overlay(
            overlay_cls.OVERLAY_ID,
            overlay_cls(
                overlay_cfg,
                self.logger,
                locked=True,
                opacity=opacity,
                windowed_overlay=windowed_overlay,
                **overlay_kwargs
            )
        )

    def _input_telemetry_update(self, data: Dict[str, Any]):
        """Send input telemetry data to input telemetry overlay."""
        self.window_manager.unicast_high_freq_data(
            InputTelemetryOverlay.OVERLAY_ID,
            InputTelemetryData.from_json(data)
        )

    def _motion_update(self, data: Dict[str, Any]):
        """Send motion data to motion overlay."""
        self.window_manager.unicast_high_freq_data(
            TrackRadarOverlay.OVERLAY_ID,
            LiveSessionMotionInfo.from_json(data)
        )

    def _set_overlays_visibility(self, visible: bool):
        self.window_manager.broadcast_data("__set_visibility__", {"visible": visible})
