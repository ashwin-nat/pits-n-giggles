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

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout

from apps.hud.common import get_ref_row
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from lib.f1_types import F1Utils

from .sector_status_bar import SectorStatusBar

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapTimerOverlay(BaseOverlay):

    OVERLAY_ID: str = "lap_timer"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int):
        """Initialize lap timer overlay.

        Args:
            config (OverlaysConfig): Overlay config
            logger (logging.Logger): Logger object
            locked (bool): Locked state
            opacity (int): Window opacity
        """

        # Overlay specific fields
        self.curr_session_uid = None
        self.curr_lap_num: Optional[int] = None

        # constants
        self._default_time_str = "--:--.---"
        self._default_delta_str = "---"
        self._base_curr_str = "Curr:   "
        self._base_last_str = "Last:   "
        self._base_best_str = "Best:   "
        self._base_delta_str = "Delta:  "
        self._base_est_str = "Est:    "

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity)
        self._init_event_handlers()
        self.curr_lap_display_timer: QTimer = QTimer(self)

    def build_ui(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        font = QFont("Consolas", 20, QFont.Bold)

        self.curr_label = QLabel(f"P{self._base_curr_str}{self._default_time_str}")
        self.curr_label.setFont(font)
        self.curr_label.setStyleSheet("color: #00FFFF;")

        self.last_label = QLabel(f"{self._base_last_str}{self._default_time_str}")
        self.last_label.setFont(font)
        self.last_label.setStyleSheet("color: #FFFFFF;")

        self.best_label = QLabel(f"{self._base_best_str}{self._default_time_str}")
        self.best_label.setFont(font)
        self.best_label.setStyleSheet("color: #00FF00;")

        self.delta_label = QLabel(f"{self._base_delta_str}{self._default_delta_str}")
        self.delta_label.setFont(font)
        self.delta_label.setStyleSheet("color: #FFFFFF;")

        self.estimated_label = QLabel(f"{self._base_est_str}{self._default_time_str}")
        self.estimated_label.setFont(font)
        self.estimated_label.setStyleSheet("color: #FFFFFF;")

        layout.addWidget(self.curr_label)
        layout.addWidget(self.last_label)
        layout.addWidget(self.best_label)
        layout.addWidget(self.estimated_label)
        layout.addWidget(self.delta_label)

        self.sector_bar = SectorStatusBar()
        layout.addWidget(self.sector_bar)

        self.setLayout(layout)

        self.resize(220, 140)

    def _init_event_handlers(self):
        """Initialize command handlers"""
        @self.on_event("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:
            """Handles race_table_update event"""
            session_type = data["event-type"]
            if session_type == 'None':
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                return

            incoming_session_uid = data.get("session-uid")
            assert (incoming_session_uid is not None)
            if (self.curr_session_uid != incoming_session_uid):
                self.clear()
                self.curr_session_uid = incoming_session_uid
                self.logger.info(f'{self.overlay_id} New session detected: {self.curr_session_uid}')

            lap_info = ref_row["lap-info"]
            last_lap = lap_info["last-lap"]
            best_lap = lap_info["best-lap"]
            curr_lap = lap_info["curr-lap"]
            self._update_last_lap(last_lap["lap-time-ms"])
            self._update_best_lap(best_lap["lap-time-ms"])

            delta = curr_lap["delta"]
            if delta is not None:
                estimated_lap_time = F1Utils.millisecondsToMinutesSecondsMilliseconds(best_lap["lap-time-ms"] + delta)
            else:
                estimated_lap_time = self._default_time_str

            incoming_lap_num = lap_info["current-lap"]
            if self._is_timer_active():
                # Last lap display timer ongoing. Display last lap time
                display_time_ms = last_lap["lap-time-ms"]
                display_sector_status = last_lap["sector-status"]
            elif self.curr_lap_num and (self.curr_lap_num != incoming_lap_num):
                # If lap number has changed, start timer to display current lap time
                self.logger.debug(f'{self.overlay_id} Detected lap number change from {self.curr_lap_num} to {incoming_lap_num}')
                self._set_timer()
                # Display last lap
                display_time_ms = last_lap["lap-time-ms"]
                display_sector_status = last_lap["sector-status"]
            elif data.get("race-ended"):
                # Race over, display last lap
                display_time_ms = last_lap["lap-time-ms"]
                display_sector_status = last_lap["sector-status"]
            else:
                # Display current lap
                display_time_ms = curr_lap["lap-time-ms"]
                display_sector_status = curr_lap["sector-status"]
            self.curr_lap_num = incoming_lap_num
            self._update_curr_lap(display_time_ms)
            self.sector_bar.set_sector_status(display_sector_status)
            self._update_delta(delta)
            self._update_estimated(estimated_lap_time)

    def clear(self):
        """Clear current lap display"""
        self.curr_label.setText(f"{self._base_curr_str}{self._default_time_str}")
        self.last_label.setText(f"{self._base_last_str}{self._default_time_str}")
        self.best_label.setText(f"{self._base_best_str}{self._default_time_str}")
        self.delta_label.setText(f"{self._base_delta_str}{self._default_delta_str}")
        self.delta_label.setStyleSheet("color: #FFFFFF;")
        self.estimated_label.setText(f"{self._base_est_str}{self._default_time_str}")
        self.sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)
        self.curr_session_uid = None
        self.curr_lap_num = None

    def _update_last_lap(self, last_lap_ms: Optional[int]):
        """Format and update last lap time"""
        time_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(last_lap_ms) \
            if last_lap_ms else self._default_time_str
        self.last_label.setText(f"{self._base_last_str}{time_str}")

    def _update_best_lap(self, best_lap_ms: Optional[int]):
        """Format and update best lap time"""
        time_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(best_lap_ms) \
            if best_lap_ms else self._default_time_str
        self.best_label.setText(f"{self._base_best_str}{time_str}")

    def _update_curr_lap(self, curr_lap_ms: Optional[int]):
        """Format and update current lap time"""
        time_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(curr_lap_ms) \
            if curr_lap_ms else self._default_time_str
        self.curr_label.setText(f"{self._base_curr_str}{time_str}")

    def _update_delta(self, delta: Optional[float]):
        """Update delta label with color"""
        if delta is None:
            self.delta_label.setText(f"{self._base_delta_str}{self._default_delta_str}")
            self.delta_label.setStyleSheet("color: #FFFFFF;")
            return

        delta_s = delta / 1000
        text = F1Utils.formatFloat(delta_s, precision=3, signed=True)
        self.delta_label.setText(f"Delta: {text}")

        if delta_s < 0:
            color = "#00FF00"     # faster
        elif delta_s > 0:
            color = "#FF5555"     # slower
        else:
            color = "#FFFFFF"
        self.delta_label.setStyleSheet(f"color: {color};")

    def _update_estimated(self, est: Optional[str]):
        """Update estimated lap time"""
        self.estimated_label.setText(f"{self._base_est_str}{est}")

    def _is_timer_active(self) -> bool:
        """Check if current lap display timer is active"""
        return self.curr_lap_display_timer.isActive()

    def _set_timer(self, interval_ms: int = 5000):
        """Start current lap display timer"""
        assert not self.curr_lap_display_timer.isActive(), "Current lap display timer is already running"
        self.curr_lap_display_timer.setSingleShot(True)
        self.curr_lap_display_timer.start(interval_ms)
        self.logger.debug(f"{self.overlay_id} Started current lap display timer with interval {interval_ms} ms")
