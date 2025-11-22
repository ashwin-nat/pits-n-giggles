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

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from apps.hud.common import get_ref_row
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from lib.f1_types import F1Utils

from .sector_status_bar import SectorStatusBar

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapTimerOverlay(BaseOverlay):
    """Overlay displaying lap timing information for racing sessions."""

    OVERLAY_ID: str = "lap_timer"

    # Display constants
    DEFAULT_TIME = "--:--.---"
    DEFAULT_DELTA = "---"
    DISPLAY_TIMER_MS = 5000
    FONT_FACE = "Formula1 Display"
    FONT_SIZE = 16

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int, scale_factor: float):
        """Initialize lap timer overlay.

        Args:
            config (OverlaysConfig): Overlay config
            logger (logging.Logger): Logger object
            locked (bool): Locked state
            opacity (int): Window opacity
            scale_factor (float): UI Scale factor (multiplier)
        """
        # Session state
        self.curr_session_uid = None
        self.curr_lap_num: Optional[int] = None

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor)
        self._init_event_handlers()
        self.curr_lap_display_timer: QTimer = QTimer(self)

    def build_ui(self):
        """Build the overlay UI components."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Create grid layout for labels
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(5)

        label_font = QFont(self.FONT_FACE, int(self.FONT_SIZE * self.scale_factor), QFont.Bold)
        value_font = QFont(self.FONT_FACE, int(self.FONT_SIZE * self.scale_factor), QFont.Bold)

        # Create fixed labels (left column)
        curr_label_fixed = self._create_label("Curr:", label_font, "#FFFFFF")
        last_label_fixed = self._create_label("Last:", label_font, "#FFFFFF")
        best_label_fixed = self._create_label("Best:", label_font, "#FFFFFF")
        est_label_fixed = self._create_label("Est:", label_font, "#FFFFFF")
        delta_label_fixed = self._create_label("Delta:", label_font, "#FFFFFF")

        # Create value labels (right column) with fixed width
        self.curr_value = self._create_fixed_width_label(self.DEFAULT_TIME, value_font, "#00FFFF")
        self.last_value = self._create_fixed_width_label(self.DEFAULT_TIME, value_font, "#FFFFFF")
        self.best_value = self._create_fixed_width_label(self.DEFAULT_TIME, value_font, "#00FF00")
        self.estimated_value = self._create_fixed_width_label(self.DEFAULT_TIME, value_font, "#FFFFFF")
        self.delta_value = self._create_fixed_width_label(self.DEFAULT_DELTA, value_font, "#FFFFFF")

        # Add to grid: row, column
        grid_layout.addWidget(curr_label_fixed, 0, 0, Qt.AlignRight)
        grid_layout.addWidget(self.curr_value, 0, 1, Qt.AlignLeft)

        grid_layout.addWidget(last_label_fixed, 1, 0, Qt.AlignRight)
        grid_layout.addWidget(self.last_value, 1, 1, Qt.AlignLeft)

        grid_layout.addWidget(best_label_fixed, 2, 0, Qt.AlignRight)
        grid_layout.addWidget(self.best_value, 2, 1, Qt.AlignLeft)

        grid_layout.addWidget(est_label_fixed, 3, 0, Qt.AlignRight)
        grid_layout.addWidget(self.estimated_value, 3, 1, Qt.AlignLeft)

        grid_layout.addWidget(delta_label_fixed, 4, 0, Qt.AlignRight)
        grid_layout.addWidget(self.delta_value, 4, 1, Qt.AlignLeft)

        # Add grid to main layout
        main_layout.addLayout(grid_layout)

        # Add sector bar
        self.sector_bar = SectorStatusBar()
        main_layout.addWidget(self.sector_bar)

        self.setLayout(main_layout)
        self.resize(260, 160)

    def _create_label(self, text: str, font: QFont, color: str) -> QLabel:
        """Create a styled label.

        Args:
            text: Label text
            font: Font to use
            color: Text color in hex format

        Returns:
            Configured QLabel instance
        """
        label = QLabel(text)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")
        return label

    def _create_fixed_width_label(self, text: str, font: QFont, color: str) -> QLabel:
        """Create a styled label with fixed minimum width to prevent resizing.

        Args:
            text: Label text
            font: Font to use
            color: Text color in hex format

        Returns:
            Configured QLabel instance with fixed width
        """
        label = QLabel(text)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")

        # Calculate width based on the widest possible content
        # Using a string of "8" characters as they tend to be widest in most fonts
        metrics = label.fontMetrics()
        max_width = metrics.horizontalAdvance("88:88.888")  # Widest time format
        delta_width = metrics.horizontalAdvance("+8.888")    # Widest delta format

        # Add padding on both sides (10 pixels on each side = 20 total)
        padding = 20
        label.setMinimumWidth(max(max_width, delta_width) + padding)

        return label

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:
            """Handle race table update events."""
            # Validate session type
            session_type = data["event-type"]
            if session_type == 'None':
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                return

            # Handle session changes
            incoming_session_uid = data["session-uid"]
            assert incoming_session_uid is not None

            if self.curr_session_uid != incoming_session_uid:
                self._handle_new_session(incoming_session_uid)

            # Extract lap information
            lap_info = ref_row["lap-info"]
            last_lap = lap_info["last-lap"]
            best_lap = lap_info["best-lap"]
            curr_lap = lap_info["curr-lap"]

            # Update static fields
            self._update_last_lap(last_lap["lap-time-ms"])
            self._update_best_lap(best_lap["lap-time-ms"])

            # Determine what to display in current lap field
            incoming_lap_num = lap_info["current-lap"]
            display_info = self._get_display_info(
                data, curr_lap, last_lap, incoming_lap_num
            )

            # Update current lap number
            self.curr_lap_num = incoming_lap_num

            # Update display based on driver status
            driver_status = curr_lap["driver-status"]
            delta = curr_lap["delta-ms"]

            if driver_status in {"FLYING_LAP", "ON_TRACK"}:
                self._display_real_lap(
                    display_info["time_ms"],
                    display_info["sector_status"],
                    delta,
                    best_lap["lap-time-ms"]
                )
            else:
                self._display_cooldown_lap(
                    driver_status,
                    display_info["sector_status"]
                )

    def _handle_new_session(self, session_uid: str):
        """Handle new session detection.

        Args:
            session_uid: New session unique identifier
        """
        self.clear()
        self.curr_session_uid = session_uid
        self.logger.info(f'{self.overlay_id} New session detected: {session_uid}')

    def _get_display_info(
        self,
        data: Dict[str, Any],
        curr_lap: Dict[str, Any],
        last_lap: Dict[str, Any],
        incoming_lap_num: int
    ) -> Dict[str, Any]:
        """Determine what lap information to display.

        Args:
            data: Race data
            curr_lap: Current lap data
            last_lap: Last lap data
            incoming_lap_num: Incoming lap number

        Returns:
            Dictionary with time_ms and sector_status to display
        """
        # Check if last lap display timer is active
        if self._is_timer_active():
            return {
                "time_ms": last_lap["lap-time-ms"],
                "sector_status": last_lap["sector-status"]
            }

        # Check for lap number change
        if self.curr_lap_num and self.curr_lap_num != incoming_lap_num:
            self.logger.debug(
                f'{self.overlay_id} Lap change: {self.curr_lap_num} -> {incoming_lap_num}'
            )
            self._start_display_timer()
            return {
                "time_ms": last_lap["lap-time-ms"],
                "sector_status": last_lap["sector-status"]
            }

        # Check if race ended
        if data.get("race-ended"):
            return {
                "time_ms": last_lap["lap-time-ms"],
                "sector_status": last_lap["sector-status"]
            }

        # Default to current lap
        return {
            "time_ms": curr_lap["lap-time-ms"],
            "sector_status": curr_lap["sector-status"]
        }

    def _display_real_lap(
        self,
        time_ms: Optional[int],
        sector_status: Any,
        delta: Optional[float],
        best_lap_ms: Optional[int]
    ):
        """Display information for a flying lap.

        Args:
            time_ms: Lap time in milliseconds
            sector_status: Sector status information
            delta: Delta time in milliseconds
            best_lap_ms: Best lap time in milliseconds
        """
        # Update current lap time
        self._update_curr_lap(time_ms)
        self.sector_bar.set_sector_status(sector_status)

        # Update delta and estimated time
        if delta is not None:
            self._update_delta(delta)
            estimated_ms = best_lap_ms + delta if best_lap_ms else None
            estimated_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(estimated_ms)
            self._update_estimated(estimated_str)
        else:
            self._clear_delta_and_estimated()

    def _display_cooldown_lap(self, driver_status: str, sector_status: Any):
        """Display information for non-flying lap status.

        Args:
            driver_status: Current driver status string
            sector_status: Sector status information
        """
        # Display driver status in current lap field
        self.curr_value.setText(driver_status)
        self.sector_bar.set_sector_status(sector_status)

        # Clear delta and estimated time
        self._clear_delta_and_estimated()

    def clear(self):
        """Reset all display fields to default values."""
        self.curr_value.setText(self.DEFAULT_TIME)
        self.curr_value.setStyleSheet("color: #00FFFF;")
        self.last_value.setText(self.DEFAULT_TIME)
        self.best_value.setText(self.DEFAULT_TIME)
        self.delta_value.setText(self.DEFAULT_DELTA)
        self.delta_value.setStyleSheet("color: #FFFFFF;")
        self.estimated_value.setText(self.DEFAULT_TIME)
        self.sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)
        self.curr_session_uid = None
        self.curr_lap_num = None

    def _update_last_lap(self, last_lap_ms: Optional[int]):
        """Update last lap time display.

        Args:
            last_lap_ms: Last lap time in milliseconds
        """
        time_str = (
            F1Utils.millisecondsToMinutesSecondsMilliseconds(last_lap_ms)
            if last_lap_ms else self.DEFAULT_TIME
        )
        self.last_value.setText(time_str)

    def _update_best_lap(self, best_lap_ms: Optional[int]):
        """Update best lap time display.

        Args:
            best_lap_ms: Best lap time in milliseconds
        """
        time_str = (
            F1Utils.millisecondsToMinutesSecondsMilliseconds(best_lap_ms)
            if best_lap_ms else self.DEFAULT_TIME
        )
        self.best_value.setText(time_str)

    def _update_curr_lap(self, curr_lap_ms: Optional[int]):
        """Update current lap time display.

        Args:
            curr_lap_ms: Current lap time in milliseconds
        """
        time_str = (
            F1Utils.millisecondsToMinutesSecondsMilliseconds(curr_lap_ms)
            if curr_lap_ms else self.DEFAULT_TIME
        )
        self.curr_value.setText(time_str)
        self.curr_value.setStyleSheet("color: #00FFFF;")

    def _update_delta(self, delta: float):
        """Update delta display with appropriate color.

        Args:
            delta: Delta time in milliseconds
        """
        delta_s = delta / 1000
        text = F1Utils.formatFloat(delta_s, precision=3, signed=True)
        self.delta_value.setText(text)

        # Set color based on delta value
        if delta_s < 0:
            color = "#00FF00"  # Faster (green)
        elif delta_s > 0:
            color = "#FF5555"  # Slower (red)
        else:
            color = "#FFFFFF"  # Neutral (white)

        self.delta_value.setStyleSheet(f"color: {color};")

    def _update_estimated(self, est: str):
        """Update estimated lap time display.

        Args:
            est: Formatted estimated time string
        """
        self.estimated_value.setText(est)

    def _clear_delta_and_estimated(self):
        """Clear delta and estimated time fields."""
        self.delta_value.setText(self.DEFAULT_DELTA)
        self.delta_value.setStyleSheet("color: #FFFFFF;")
        self.estimated_value.setText(self.DEFAULT_TIME)

    def _is_timer_active(self) -> bool:
        """Check if lap display timer is currently active.

        Returns:
            True if timer is active, False otherwise
        """
        return self.curr_lap_display_timer.isActive()

    def _start_display_timer(self):
        """Start the lap display timer."""
        assert not self.curr_lap_display_timer.isActive(), \
            "Display timer is already running"

        self.curr_lap_display_timer.setSingleShot(True)
        self.curr_lap_display_timer.start(self.DISPLAY_TIMER_MS)
        self.logger.debug(
            f"{self.overlay_id} Started display timer ({self.DISPLAY_TIMER_MS}ms)"
        )
