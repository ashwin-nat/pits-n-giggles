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
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QTimer

from apps.hud.common import get_ref_row, is_race_type_session
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import LAP_TIMER_OVERLAY_ID, OverlayPosition
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapTimerOverlay(BaseOverlayQML):
    """QML-based overlay displaying lap timing information for racing sessions."""

    OVERLAY_ID: str = LAP_TIMER_OVERLAY_ID
    QML_FILE: Path = Path(__file__).parent / "lap_timer_overlay.qml"

    # Display constants
    DEFAULT_TIME = "--:--.---"
    DEFAULT_DELTA = "---"
    DEFAULT_SECTOR_STATUS = [F1Utils.SECTOR_STATUS_NA] * 3

    def __init__(self,
                 config: OverlayPosition,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool,
                 ):
        """Initialize lap timer overlay.

        Args:
            config (OverlaysConfig): Overlay config
            logger (logging.Logger): Logger object
            locked (bool): Locked state
            opacity (int): Window opacity
            scale_factor (float): UI Scale factor (multiplier)
            windowed_overlay (bool): Windowed overlay
        """
        # Session state
        self.curr_session_uid = None
        self.last_lap_num: Optional[int] = None
        self.show_last_lap_sector_bar = False

        # Timer for last lap sector display
        self.last_sector_display_timer = QTimer()
        self.last_sector_display_timer.setSingleShot(True)
        self.last_sector_display_timer.timeout.connect(self._timer_clear_cb)

        super().__init__(
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
            refresh_interval_ms=None  # Event-driven, no fixed refresh
        )

        self._init_event_handlers()

    def render_frame(self):
        """Not used - this overlay is event-driven."""
        pass

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:
            """Handle race table update events."""
            if not self._root:
                self.logger.debug(f"{self.OVERLAY_ID} | Overlay not initialized yet")
                return

            session_type = data["event-type"]
            if session_type == "None":
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                return

            # Handle session changes
            incoming_session_uid = data["session-uid"]
            assert incoming_session_uid is not None
            if self.curr_session_uid != incoming_session_uid:
                self._handle_new_session(incoming_session_uid)

            lap_info = ref_row["lap-info"]
            last_lap = lap_info["last-lap"]
            best_lap = lap_info["best-lap"]
            curr_lap = lap_info["curr-lap"]
            sc_status = data["safety-car-status"]

            # Update static fields
            self._update_last_lap(last_lap["lap-time-ms"])
            self._update_best_lap(best_lap["lap-time-ms"])
            self._update_sector_status("lastSectorStatus", last_lap["sector-status"])
            self._update_sector_status("bestSectorStatus", best_lap["sector-status"])

            # Handle lap number changes
            if self.last_lap_num and self.last_lap_num != lap_info["current-lap"]:
                self.logger.debug(f"{self.OVERLAY_ID} | Lap number changed from "
                                  f"{self.last_lap_num} to {lap_info['current-lap']}")
                # Start 5 sec last-lap sector bar window
                self.show_last_lap_sector_bar = True
                self.last_sector_display_timer.start(5000)

            # Update current sector bar
            if self.show_last_lap_sector_bar:
                self._update_sector_status("currentSectorStatus", last_lap["sector-status"])
            else:
                self._update_sector_status("currentSectorStatus", curr_lap["sector-status"])

            self.last_lap_num = lap_info["current-lap"]

            self._handle_current_lap_display(curr_lap, session_type, sc_status)
            self._handle_delta_and_estimated(curr_lap, best_lap, sc_status)

    def _handle_current_lap_display(self, curr_lap: Dict[str, Any], session_type: str, sc_status: str) -> None:
        """Handle current lap display.
        On FP/Quali, If on flying lap, display curr lap time, else display status
        In races, always display everything live
        """
        driver_status = curr_lap["driver-status"]
        if is_race_type_session(session_type):
            # In races, ignore driver_status completely, only consider sc status
            if self._is_safety_car(sc_status):
                self._update_curr_lap_str("VSC" if sc_status == "VIRTUAL_SAFETY_CAR" else "SC")
            else:
                self._update_curr_lap(curr_lap["lap-time-ms"])

        elif driver_status in {"FLYING_LAP", "ON_TRACK"}:
            # Non-race sessions: only update when active
            self._update_curr_lap(curr_lap["lap-time-ms"])

        else:
            self._update_curr_lap_str(driver_status)

    def _handle_delta_and_estimated(
        self,
        curr_lap: Dict[str, Any],
        best_lap: Dict[str, Any],
        sc_status: str
    ) -> None:
        """Handle delta and estimated time calculations."""
        is_sc = self._is_safety_car(sc_status)
        best_ms = best_lap["lap-time-ms"] or 0
        delta_ms_for_estimated = None

        # SC delta takes priority
        if is_sc:
            delta_sc = curr_lap["delta-sc-sec"]
            if delta_sc is not None:
                self._update_delta_sec(delta_sc, is_sc=True)
                delta_ms_for_estimated = int(delta_sc * 1000)
            else:
                self._clear_delta()
        else:
            # Normal racing delta
            delta_ms = curr_lap["delta-ms"]
            if delta_ms is not None:
                self._update_delta_ms(delta_ms, is_sc=False)
                delta_ms_for_estimated = delta_ms
            else:
                self._clear_delta()

        # Always update estimated time
        if best_ms and delta_ms_for_estimated is not None:
            estimated_ms = best_ms + delta_ms_for_estimated
            est_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(estimated_ms)
        else:
            est_str = self.DEFAULT_TIME
        self._update_estimated(est_str)

    def _handle_new_session(self, session_uid: str):
        """Handle new session detection.

        Args:
            session_uid: New session unique identifier
        """
        self.clear()
        self.curr_session_uid = session_uid
        self.logger.info(f'{self.OVERLAY_ID} New session detected: {session_uid}')

    def clear(self):
        """Reset all display fields to default values."""
        self._root.setProperty("currentTime", self.DEFAULT_TIME)
        self._root.setProperty("currentColor", "#00FFFF")
        self._root.setProperty("lastTime", self.DEFAULT_TIME)
        self._root.setProperty("bestTime", self.DEFAULT_TIME)
        self._root.setProperty("deltaTime", self.DEFAULT_DELTA)
        self._root.setProperty("deltaColor", "#FFFFFF")
        self._root.setProperty("estimatedTime", self.DEFAULT_TIME)
        self._root.setProperty("currentSectorStatus", self.DEFAULT_SECTOR_STATUS)
        self._root.setProperty("lastSectorStatus", self.DEFAULT_SECTOR_STATUS)
        self._root.setProperty("bestSectorStatus", self.DEFAULT_SECTOR_STATUS)

        self.curr_session_uid = None
        self.show_last_lap_sector_bar = False

    def _update_last_lap(self, last_lap_ms: Optional[int]):
        """Update last lap time display.

        Args:
            last_lap_ms: Last lap time in milliseconds
        """
        time_str = (
            F1Utils.millisecondsToMinutesSecondsMilliseconds(last_lap_ms)
            if last_lap_ms else self.DEFAULT_TIME
        )
        self._root.setProperty("lastTime", time_str)

    def _update_best_lap(self, best_lap_ms: Optional[int]):
        """Update best lap time display.

        Args:
            best_lap_ms: Best lap time in milliseconds
        """
        time_str = (
            F1Utils.millisecondsToMinutesSecondsMilliseconds(best_lap_ms)
            if best_lap_ms else self.DEFAULT_TIME
        )
        self._root.setProperty("bestTime", time_str)

    def _update_curr_lap(self, curr_lap_ms: Optional[int]):
        """Update current lap time display.

        Args:
            curr_lap_ms: Current lap time in milliseconds
        """
        time_str = (
            F1Utils.millisecondsToMinutesSecondsMilliseconds(curr_lap_ms)
            if curr_lap_ms else self.DEFAULT_TIME
        )
        self._update_curr_lap_str(time_str)

    def _update_curr_lap_str(self, time_str: str):
        """Update current lap display with string."""

        self._root.setProperty("currentTime", time_str)
        self._root.setProperty("currentColor", "#00FFFF")

    def _update_delta_ms(self, delta_ms: int, is_sc: bool):
        """Update delta display with appropriate color.

        Args:
            delta_ms: Delta time in milliseconds
            is_sc: Is safety car
        """
        delta_s = delta_ms / 1000
        self._update_delta_sec(delta_s, is_sc)

    def _update_delta_sec(self, delta_sec: float, is_sc: bool):
        """Update delta display with appropriate color.

        Args:
            delta_sec: Delta time in seconds
            is_sc: Is safety car
        """
        text = F1Utils.formatFloat(delta_sec, precision=3, signed=True)

        # Under SC: positive (or zero) is good
        # Racing: negative is good
        is_good = (delta_sec < 0) != is_sc
        color = "#00FF00" if is_good else "#FF5555"

        self._root.setProperty("deltaTime", text)
        self._root.setProperty("deltaColor", color)

    def _update_estimated(self, est: str):
        """Update estimated lap time display.

        Args:
            est: Formatted estimated time string
        """
        self._root.setProperty("estimatedTime", est)

    def _clear_delta(self):
        """Clear delta field."""
        self._root.setProperty("deltaTime", self.DEFAULT_DELTA)
        self._root.setProperty("deltaColor", "#FFFFFF")

    def _update_sector_status(self, property_name: str, status_list: List[int]):
        """Update sector status bar.

        Args:
            property_name: QML property name (currentSectorStatus, lastSectorStatus, bestSectorStatus)
            status_list: List of 3 sector status values
        """
        if len(status_list) == 3:
            self._root.setProperty(property_name, status_list)

    def _timer_clear_cb(self):
        """Clear the last lap sector bar flag"""
        self.show_last_lap_sector_bar = False
        # Clear the sector bar back to current lap
        self._root.setProperty("currentSectorStatus", self.DEFAULT_SECTOR_STATUS)

    def _is_safety_car(self, status: str) -> bool:
        """Check if the session is in racing or safety car state."""
        return status in {"FULL_SAFETY_CAR", "VIRTUAL_SAFETY_CAR"}
