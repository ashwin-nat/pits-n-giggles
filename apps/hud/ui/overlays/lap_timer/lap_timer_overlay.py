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

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QVBoxLayout)

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
    FONT_FACE = "Formula1 Display"
    FONT_SIZE_LABEL = 12
    FONT_SIZE_VALUE = 14

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

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor)
        self._init_event_handlers()

    def build_ui(self):
        """Build the overlay UI components."""
        self.logger.debug(f'{self.overlay_id} | Building UI')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        label_font = QFont(self.FONT_FACE, int(self.FONT_SIZE_LABEL * self.scale_factor))
        value_font = QFont(self.FONT_FACE, int(self.FONT_SIZE_VALUE * self.scale_factor), QFont.Bold)

        # 2x2 Grid of cards
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        # Create cards: Current (top-left), Delta (top-right), Last (bottom-left), Best (bottom-right)
        self.curr_value = self._create_card(grid, "CURRENT", self.DEFAULT_TIME,
                                            label_font, value_font, "#00FFFF", 0, 0)
        self.delta_value = self._create_card(grid, "DELTA", self.DEFAULT_DELTA,
                                              label_font, value_font, "#FFFFFF", 0, 1)
        self.last_value = self._create_card(grid, "LAST", self.DEFAULT_TIME,
                                             label_font, value_font, "#FFFFFF", 1, 0)
        self.best_value = self._create_card(grid, "BEST", self.DEFAULT_TIME,
                                             label_font, value_font, "#00FF00", 1, 1)

        main_layout.addLayout(grid)

        # Estimated time (full width bar with horizontal layout)
        est_container = QFrame()
        est_container.setMinimumHeight(42)
        est_layout = QHBoxLayout(est_container)
        est_layout.setContentsMargins(8, 5, 8, 5)
        est_layout.setSpacing(5)

        est_label = QLabel("ESTIMATED:")
        est_label.setFont(label_font)
        est_label.setStyleSheet("color: #888888;")
        est_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.estimated_value = QLabel(self.DEFAULT_TIME)
        self.estimated_value.setFont(value_font)
        self.estimated_value.setStyleSheet("color: #FFFFFF;")
        self.estimated_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        est_layout.addWidget(est_label)
        est_layout.addWidget(self.estimated_value)
        main_layout.addWidget(est_container)

        # Sector bar at bottom
        self.sector_bar = SectorStatusBar()
        main_layout.addWidget(self.sector_bar)

        self.setLayout(main_layout)

    def _create_card(self, grid: QGridLayout, label_text: str, default_value: str,
                     label_font: QFont, value_font: QFont, value_color: str,
                     row: int, col: int) -> QLabel:
        """Create a card with label and value.

        Args:
            grid: Grid layout to add card to
            label_text: Label text
            default_value: Default value text
            label_font: Font for label
            value_font: Font for value
            value_color: Color for value
            row: Grid row
            col: Grid column

        Returns:
            The value QLabel
        """
        card = QFrame()
        card.setMinimumSize(165, 52)
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("QFrame { border: 1px solid #333333; background-color: #1a1a1a; }")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(6, 5, 6, 5)
        card_layout.setSpacing(2)

        label = QLabel(label_text)
        label.setFont(label_font)
        label.setStyleSheet("color: #888888; border: none;")
        label.setAlignment(Qt.AlignCenter)

        value = QLabel(default_value)
        value.setFont(value_font)
        value.setStyleSheet(f"color: {value_color}; border: none;")
        value.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(label)
        card_layout.addWidget(value)

        grid.addWidget(card, row, col)
        return value

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

            # Update display based on driver status
            driver_status = curr_lap["driver-status"]
            delta = curr_lap["delta-ms"]

            self.sector_bar.set_sector_status(curr_lap["sector-status"])

            if driver_status in {"FLYING_LAP", "ON_TRACK"}:
                # Update current lap time
                self._update_curr_lap(curr_lap["lap-time-ms"])

                # Update delta and estimated time
                if delta is not None:
                    self._update_delta(delta)
                    estimated_ms = best_lap["lap-time-ms"] + delta if best_lap["lap-time-ms"] else None
                    estimated_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(estimated_ms)
                    self._update_estimated(estimated_str)
                else:
                    self._clear_delta_and_estimated()
            else:
                # Display driver status in current lap field
                self.curr_value.setText(driver_status)
                self.curr_value.setStyleSheet("color: #00FFFF; border: none;")

                # Clear delta and estimated for non-flying laps
                self._clear_delta_and_estimated()

    def _handle_new_session(self, session_uid: str):
        """Handle new session detection.

        Args:
            session_uid: New session unique identifier
        """
        self.clear()
        self.curr_session_uid = session_uid
        self.logger.info(f'{self.overlay_id} New session detected: {session_uid}')

    def clear(self):
        """Reset all display fields to default values."""
        self.curr_value.setText(self.DEFAULT_TIME)
        self.curr_value.setStyleSheet("color: #00FFFF; border: none;")
        self.last_value.setText(self.DEFAULT_TIME)
        self.best_value.setText(self.DEFAULT_TIME)
        self.delta_value.setText(self.DEFAULT_DELTA)
        self.delta_value.setStyleSheet("color: #FFFFFF; border: none;")
        self.estimated_value.setText(self.DEFAULT_TIME)
        self.sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)
        self.curr_session_uid = None

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
        self.curr_value.setStyleSheet("color: #00FFFF; border: none;")

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

        self.delta_value.setStyleSheet(f"color: {color}; border: none;")

    def _update_estimated(self, est: str):
        """Update estimated lap time display.

        Args:
            est: Formatted estimated time string
        """
        self.estimated_value.setText(est)

    def _clear_delta_and_estimated(self):
        """Clear delta and estimated time fields."""
        self.delta_value.setText(self.DEFAULT_DELTA)
        self.delta_value.setStyleSheet("color: #FFFFFF; border: none;")
        self.estimated_value.setText(self.DEFAULT_TIME)
