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
import os
from typing import Any, Dict, List, Optional, Type

from apps.hud.common import get_ref_row, get_ref_row_index, is_tt_session
from apps.hud.ui.overlays import (BaseOverlay, CircuitInfoOverlay, HudOverlay,
                                  InputTelemetryOverlay, LapTimerOverlay,
                                  MfdOverlay, PuOverlay, TimingTowerOverlay,
                                  TrackRadarOverlay)
from apps.hud.ui.overlays.mfd.pages import (FuelInfoPage, LapTimesPage,
                                            MfdPageBase, PaceCompPage,
                                            PitRejoinPredictionPage,
                                            StandalonePageHost,
                                            TrafficMonitorPage, TyreInfoPage,
                                            TyreSetsPage, WeatherForecastPage)
from lib.assets_loader import load_fonts
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import OverlayPosition, PngSettings
from lib.rate_limiter import RateLimiter
from lib.wdt import WatchDogTimerSync

from .hf_types import HudOverlayData, InputTelemetryData, LiveSessionMotionInfo
from .window_mgr import WindowManager

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class OverlaysMgr:

    OVERLAY_CLASSES: List[Type[BaseOverlay]] = [
        LapTimerOverlay, TimingTowerOverlay, InputTelemetryOverlay, TrackRadarOverlay,
        HudOverlay, CircuitInfoOverlay, PuOverlay, MfdOverlay,
    ]
    STANDALONE_PAGE_CLASSES: List[Type[MfdPageBase]] = [
        FuelInfoPage, TyreInfoPage, LapTimesPage, WeatherForecastPage,
        PitRejoinPredictionPage, TyreSetsPage, PaceCompPage, TrafficMonitorPage,
    ]

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
        if settings.Display.use_cpu_acceleration:
            os.environ["QT_QUICK_BACKEND"] = "software"
            logger.debug("Using software backend")

        self.logger = logger
        self.debug_mode = debug
        self.running = False
        self.rate_limiter = RateLimiter(interval_ms=settings.Display.refresh_interval)
        self._local_wdt_ok: bool = False
        self._auto_hide_in_menu: bool = settings.HUD.auto_hide_in_menu
        self._telemetry_active: Optional[bool] = None
        self.wdt = WatchDogTimerSync(
            status_callback=self._wdt_status_callback,
            timeout=settings.Display.wdt_timeout,
        ) if settings.Display.wdt_timeout is not None else None

        assert settings.HUD.enabled, "HUD must be enabled to run overlays manager"
        self.window_manager = WindowManager(logger, notify_parent_init_complete)
        load_fonts(debug_log_printer=self.logger.debug, error_log_printer=self.logger.error)

        enabled = settings.HUD.enabled_overlays_by_id()

        for cls in self.OVERLAY_CLASSES:
            if cls.OVERLAY_ID in enabled:
                self.window_manager.register_overlay(cls.OVERLAY_ID, cls(settings, self.logger))
            else:
                self.logger.debug("%s overlay is disabled", cls.OVERLAY_ID)

        for page_cls in self.STANDALONE_PAGE_CLASSES:
            if page_cls.OVERLAY_ID in enabled:
                page = page_cls.from_settings(settings, self.logger)
                host = StandalonePageHost(
                    page, settings, self.logger,
                    show_title_bar=page_cls.standalone_show_title(settings),
                )
                self.window_manager.register_overlay(page_cls.OVERLAY_ID, host)
            else:
                self.logger.debug("%s overlay is disabled", page_cls.OVERLAY_ID)

        self.logger.debug("Overlays manager initialized")

    def run(self):
        """Start the overlays manager"""
        self.running = True
        if self.wdt:
            self.wdt.start()
        self.window_manager.run()

    def stop(self):
        """Stop the overlays manager"""
        self.running = False
        if self.wdt:
            self.wdt.stop()
        self.window_manager.stop()

    # ------------------------------------- CONTROL REQUESTS -----------------------------------------------------------

    def get_overlay_stats(self) -> Dict[str, Any]:
        """Get current stats for all overlays

        Returns:
            Dict[str, Any]: A dictionary containing stats for each overlay
        """
        return {
            overlay_id: self._get_overlay_stats(overlay_id)
            for overlay_id in self.window_manager.overlays
        }

    def get_window_mgr_stats(self) -> Dict[str, Any]:
        """Get current stats for all overlays

        Returns:
            Dict[str, Any]: A dictionary containing stats for each overlay
        """
        return self.window_manager.get_stats()

    # -------------------------------------- DATA EVENTS ---------------------------------------------------------------

    def race_table_update(self, data: Dict[str, Any]):
        """Handle race table update"""
        if self.wdt:
            self.wdt.kick()
        self._prep_race_table_data(data)
        self.window_manager.emit_event('race_table_update', data)
        self._handle_in_menu_status(data)

    def stream_overlays_update(self, data):
        """Handle the stream overlay update event"""
        self._input_telemetry_update(data)
        self._motion_update(data)
        self._hud_overlay_update(data)
        if self.rate_limiter.allows("stream-overlay-update"):
            self.window_manager.emit_event('stream_overlay_update', data)

    # -------------------------------------- CONTROL EVENTS ------------------------------------------------------------

    def toggle_overlays_visibility(self, oid: Optional[str] = ''):
        """Toggle overlays visibility"""

        self.logger.debug("Toggling overlays visibility. oid=%s", oid)
        if oid:
            self.window_manager.unicast_event(oid, '__toggle_visibility__', {}, high_prio=True)
        else:
            self.window_manager.emit_event('__toggle_visibility__', {}, high_prio=True)

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
            self.window_manager.emit_event("__set_locked_state__", args, high_prio=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
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
                layout[overlay_id] = curr_params.toJSON() if curr_params else {}

            except Exception as e:  # pylint: disable=broad-exception-caught
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
        self.logger.debug("Setting overlays opacity to %s%%", opacity)
        self.window_manager.emit_event('__set_opacity__', {'opacity': opacity}, high_prio=True)

    def next_page(self):
        """Go to the next page in MFD overlay"""
        self.window_manager.unicast_event(MfdOverlay.OVERLAY_ID, 'next_page', {})

    def prev_page(self):
        """Go to the previous page in MFD overlay"""
        self.window_manager.unicast_event(MfdOverlay.OVERLAY_ID, 'prev_page', {})

    def mfd_interact(self):
        """Interact with MFD overlay"""
        self.window_manager.emit_event('mfd_interact', {})

    def set_overlays_layout(self, layout: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Apply overlays layout to specified overlays

        Args:
            layout (Dict[str, Dict[str, int]]): A dictionary mapping overlay IDs to their
                new layout parameters (x, y, scale_factor)

        Returns:
            Dict[str, Any]: A response dictionary indicating success or failure
        """
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
                self.window_manager.unicast_event(
                    overlay_id,
                    "__set_config__",
                    overlay_layout,
                    high_prio=True,
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
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

        self.logger.debug("Setting overlay %s scale factor to %s", oid, scale_factor)
        self.window_manager.unicast_event(oid, '__set_scale_factor__', {'scale_factor': scale_factor})

    def set_track_radar_idle_opacity(self, opacity: int):
        self.logger.debug("Setting track radar idle opacity to %s%%", opacity)
        self.window_manager.unicast_event(
            overlay_id=TrackRadarOverlay.OVERLAY_ID,
            event='set_track_radar_idle_opacity',
            data={'opacity': opacity},
            high_prio=True,
        )

    def set_track_radar_range(self, range_m: float):
        self.logger.debug("Setting track radar range to %sm", range_m)
        self.window_manager.unicast_event(
            overlay_id=TrackRadarOverlay.OVERLAY_ID,
            event='set_track_radar_range',
            data={'range_m': range_m},
            high_prio=True,
        )

    def set_circuit_info_length(self, length: int):
        self.logger.debug("Setting circuit info length to %spx", length)
        self.window_manager.unicast_event(
            overlay_id=CircuitInfoOverlay.OVERLAY_ID,
            event='set_circuit_info_length',
            data={'length': length},
            high_prio=True,
        )

    # -------------------------------------- HELPERS -------------------------------------------------------------------

    def _get_window_info(self, overlay_id: str, timeout_ms: int = 5000) -> Optional[OverlayPosition]:
        """Thread-safe query for specific window info."""
        self.logger.debug("Requesting window info for %s", overlay_id)
        ret = self.window_manager.request(overlay_id, "get_window_info", timeout_ms=timeout_ms)
        if not ret:
            return None
        return OverlayPosition.fromJSON(ret)

    def _get_overlay_stats(self, overlay_id: str, timeout_ms: int = 5000) -> Optional[Dict[str, Any]]:
        """Thread-safe query for specific window info."""
        self.logger.debug("Requesting window stats for %s", overlay_id)
        return self.window_manager.request(overlay_id, "get_window_stats", timeout_ms=timeout_ms)

    def _input_telemetry_update(self, data: Dict[str, Any]):
        """Send input telemetry data to input telemetry overlay."""
        self.window_manager.send_high_freq_data(InputTelemetryData, data)

    def _motion_update(self, data: Dict[str, Any]):
        """Send motion data to motion overlay."""
        self.window_manager.send_high_freq_data(LiveSessionMotionInfo, data)

    def _hud_overlay_update(self, data: Dict[str, Any]):
        """Send HUD data to HUD overlay."""
        self.window_manager.send_high_freq_data(HudOverlayData, data)

    def _set_overlays_visibility(self, visible: bool):
        self.window_manager.emit_event("__set_visibility__", {"visible": visible}, high_prio=True)

    def _set_telemetry_active(self, active: bool):
        if active == self._telemetry_active:
            return
        self._telemetry_active = active
        self.window_manager.emit_event("__set_telemetry_active__", {"active": active}, high_prio=True)

    def _wdt_status_callback(self, active: bool):
        """Watchdog status callback. Tracks local WDT (data arriving from core)."""
        self.logger.debug("Local WDT status: %s", active)
        self._local_wdt_ok = active
        self._update_telemetry_active()

    def _handle_in_menu_status(self, data: Dict[str, Any]):
        """Hide overlays when backend reports in-menu state; restore when session resumes."""
        if not self._auto_hide_in_menu:
            return
        if data.get("in-menu", False):
            self._set_telemetry_active(False)
            return

        if not data.get("is-spectating", False):
            session_type = data["event-type"]
            driver_status = None
            if is_tt_session(session_type):
                driver_status = data.get("tt-data", {}).get("driver-status")
            else:
                ref_row = get_ref_row(data)
                # In FP/Quali the player may be parked in garage and navigating menus
                # while periodic data keeps arriving — hide overlays in that case
                if ref_row:
                    lap_info = ref_row.get("lap-info", {})
                    curr_lap = lap_info.get("curr-lap", {})
                    driver_status = curr_lap.get("driver-status")

            if driver_status == "IN_GARAGE":
                self._set_telemetry_active(False)
                return

        self._update_telemetry_active()

    def _update_telemetry_active(self):
        """Set telemetry active state based on local WDT."""
        self._set_telemetry_active(True if self.wdt is None else self._local_wdt_ok)

    def _prep_race_table_data(self, data: Dict[str, Any]):
        """Prepare race table data for overlays."""
        table_entries: List[Dict[str, Any]] = data.get("table-entries", [])
        table_entries.sort(key=lambda x: x["driver-info"]["position"])
        ref_row_idx = get_ref_row_index(data)
        data["ref-row-index"] = ref_row_idx
