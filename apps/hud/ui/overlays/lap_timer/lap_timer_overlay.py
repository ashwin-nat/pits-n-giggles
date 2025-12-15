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
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QVBoxLayout)

from apps.hud.common import get_ref_row, is_race_type_session
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlayWidget
from lib.f1_types import F1Utils

from .sector_status_bar import SectorStatusBar

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapTimerOverlay(BaseOverlayWidget):
    """Overlay displaying lap timing information for racing sessions."""

    OVERLAY_ID: str = "lap_timer"

    # Display constants
    DEFAULT_TIME = "--:--.---"
    DEFAULT_DELTA = "---"
    FONT_FACE = "Formula1 Display"
    FONT_SIZE_LABEL = 12
    FONT_SIZE_VALUE = 14

    def __init__(self,
                 config: OverlaysConfig,
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

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor, windowed_overlay)

        self.last_lap_num: Optional[int] = None
        self.last_sector_display_timer = QTimer()
        self.last_sector_display_timer.setSingleShot(True)
        self.show_last_lap_sector_bar = False
        self.last_sector_display_timer.timeout.connect(self._timer_clear_cb)

        self._init_event_handlers()

    def build_ui(self):
        """Build the overlay UI components."""
        self.logger.debug(f'{self.overlay_id} | Building UI')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        main_layout.setSpacing(self.spacing)

        label_font = QFont(self.FONT_FACE, self.font_size_label)
        value_font = QFont(self.FONT_FACE, self.font_size_value, QFont.Bold)

        # 2x2 Grid of cards
        grid = QGridLayout()
        grid.setHorizontalSpacing(self.card_spacing)
        grid.setVerticalSpacing(self.card_spacing)

        # Create cards: Current (top-left), Delta (top-right), Last (bottom-left), Best (bottom-right)
        self.curr_value = self._create_card(grid, "CURRENT", self.DEFAULT_TIME,
                                            label_font, value_font, "#00FFFF", 0, 0)
        self.delta_value = self._create_card(grid, "DELTA", self.DEFAULT_DELTA,
                                              label_font, value_font, "#FFFFFF", 0, 1)
        self.last_value, self.last_sector_bar = self._create_card_with_sector_bar(
            grid, "LAST", self.DEFAULT_TIME,
            label_font, value_font, "#FFFFFF", 1, 0
        )

        self.best_value, self.best_sector_bar = self._create_card_with_sector_bar(
            grid, "BEST", self.DEFAULT_TIME,
            label_font, value_font, "#00FF00", 1, 1
        )

        main_layout.addLayout(grid)

        # Estimated time (full width bar with horizontal layout)
        est_container = QFrame()
        est_container.setMinimumHeight(self.est_container_min_height)
        est_layout = QHBoxLayout(est_container)
        est_layout.setContentsMargins(
            self.est_container_padding,
            self.est_container_padding_vertical,
            self.est_container_padding,
            self.est_container_padding_vertical
        )
        est_layout.setSpacing(self.est_container_spacing)

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
        self.sector_bar = SectorStatusBar(self.scale_factor)
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
        card.setMinimumSize(self.card_min_width, self.card_min_height)
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("QFrame { border: 1px solid #333333; background-color: #1a1a1a; }")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            self.card_padding,
            self.card_padding_vertical,
            self.card_padding,
            self.card_padding_vertical
        )
        card_layout.setSpacing(self.card_content_spacing)

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

    def _create_card_with_sector_bar(
        self,
        grid: QGridLayout,
        label_text: str,
        default_value: str,
        label_font: QFont,
        value_font: QFont,
        value_color: str,
        row: int,
        col: int
    ):
        card = QFrame()
        card.setMinimumSize(self.card_min_width, self.card_min_height + int(20 * self.scale_factor))
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet("QFrame { border: 1px solid #333333; background-color: #1a1a1a; }")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            self.card_padding,
            self.card_padding_vertical,
            self.card_padding,
            self.card_padding_vertical
        )
        layout.setSpacing(self.card_content_spacing)

        # Label
        label = QLabel(label_text)
        label.setFont(label_font)
        label.setStyleSheet("color: #888888; border: none;")
        label.setAlignment(Qt.AlignCenter)

        # Lap time value
        value = QLabel(default_value)
        value.setFont(value_font)
        value.setStyleSheet(f"color: {value_color}; border: none;")
        value.setAlignment(Qt.AlignCenter)

        # Sector bar
        sector_bar = SectorStatusBar(self.scale_factor * 0.75)
        sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)

        # Add to layout
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addWidget(sector_bar)

        # Add to grid
        grid.addWidget(card, row, col)

        return value, sector_bar

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:
            """Handle race table update events."""
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

            # Update static fields
            self._update_last_lap(last_lap["lap-time-ms"])
            self._update_best_lap(best_lap["lap-time-ms"])
            self.last_sector_bar.set_sector_status(last_lap["sector-status"])
            self.best_sector_bar.set_sector_status(best_lap["sector-status"])

            if self.last_lap_num and self.last_lap_num != lap_info["current-lap"]:
                self.logger.debug(f"{self.overlay_id} | Lap number changed from "
                                  f"{self.last_lap_num} to {lap_info['current-lap']}")
                # --- Start 5 sec last-lap sector bar window ---
                self.show_last_lap_sector_bar = True
                self.last_sector_display_timer.start(5000)

            if self.show_last_lap_sector_bar:
                self.sector_bar.set_sector_status(last_lap["sector-status"])
            else:
                self.sector_bar.set_sector_status(curr_lap["sector-status"])
            self.last_lap_num = lap_info["current-lap"]

            self._handle_current_lap_display(curr_lap, session_type)
            self._handle_delta_and_estimated(data, curr_lap, best_lap)

    def _handle_current_lap_display(self, curr_lap: Dict[str, Any], session_type: str) -> None:
        """Handle current lap display.
        On FP/Quali, If on flying lap, display curr lap time, else display status
        In races, always display every thing live
        """
        driver_status = curr_lap["driver-status"]
        if is_race_type_session(session_type):
            # In races, ignore driver_status completely
            self._update_curr_lap(curr_lap["lap-time-ms"])

        elif driver_status in {"FLYING_LAP", "ON_TRACK"}:
            # Non-race sessions: only update when active
            self._update_curr_lap(curr_lap["lap-time-ms"])

        else:
            self.curr_value.setText(driver_status)
            self.curr_value.setStyleSheet("color: #00FFFF; border: none;")

    def _handle_delta_and_estimated(
        self,
        data: Dict[str, Any],
        curr_lap: Dict[str, Any],
        best_lap: Dict[str, Any],
    ) -> None:

        is_sc = data["safety-car-status"] in {
            "FULL_SAFETY_CAR",
            "VIRTUAL_SAFETY_CAR",
        }

        best_ms = best_lap["lap-time-ms"] or 0
        delta_ms_for_estimated = None

        # --- SC delta takes priority ---
        if is_sc:
            delta_sc = curr_lap["delta-sc-sec"]
            if delta_sc is not None:
                self._update_delta_sec(delta_sc, is_sc=True)
                delta_ms_for_estimated = int(delta_sc * 1000)
            else:
                self._clear_delta()
        else:
            # --- Normal racing delta ---
            delta_ms = curr_lap["delta-ms"]
            if delta_ms is not None:
                self._update_delta_ms(delta_ms, is_sc=False)
                delta_ms_for_estimated = delta_ms
            else:
                self._clear_delta()

        # --- Always update estimated time ---
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
        self.show_last_lap_sector_bar = False
        self.last_sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)
        self.best_sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)

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
        self.delta_value.setText(text)

        # Under SC: positive (or zero) is good
        # Racing: negative is good
        is_good = (delta_sec < 0) != is_sc
        color = "#00FF00" if is_good else "#FF5555"

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

    def _clear_delta(self):
        """Clear delta field."""
        self.delta_value.setText(self.DEFAULT_DELTA)
        self.delta_value.setStyleSheet("color: #FFFFFF; border: none;")

    def _clear_estimated(self):
        """Clear estimated field."""
        self.estimated_value.setText(self.DEFAULT_TIME)

    @property
    def font_size_label(self) -> int:
        """Get the font size based on the scale factor."""
        return int(self.FONT_SIZE_LABEL * self.scale_factor)

    @property
    def font_size_value(self) -> int:
        """Get the font size based on the scale factor."""
        return int(self.FONT_SIZE_VALUE * self.scale_factor)

    @property
    def scaled(self) -> int:
        """Scale an integer value by scale_factor."""
        def scale_value(value: int) -> int:
            return int(value * self.scale_factor)
        return scale_value

    # Or create specific scaled properties:
    @property
    def margin(self) -> int:
        """Get scaled margin."""
        return int(10 * self.scale_factor)

    @property
    def spacing(self) -> int:
        """Get scaled spacing."""
        return int(8 * self.scale_factor)

    @property
    def card_spacing(self) -> int:
        """Get scaled card spacing."""
        return int(8 * self.scale_factor)

    @property
    def card_min_width(self) -> int:
        """Get scaled card minimum width."""
        return int(165 * self.scale_factor)

    @property
    def card_min_height(self) -> int:
        """Get scaled card minimum height."""
        return int(52 * self.scale_factor)

    @property
    def card_padding(self) -> int:
        """Get scaled card padding."""
        return int(6 * self.scale_factor)

    @property
    def card_padding_vertical(self) -> int:
        """Get scaled card vertical padding."""
        return int(5 * self.scale_factor)

    @property
    def card_content_spacing(self) -> int:
        """Get scaled card content spacing."""
        return int(2 * self.scale_factor)

    @property
    def est_container_min_height(self) -> int:
        """Get scaled estimated container minimum height."""
        return int(42 * self.scale_factor)

    @property
    def est_container_padding(self) -> int:
        """Get scaled estimated container padding."""
        return int(8 * self.scale_factor)

    @property
    def est_container_padding_vertical(self) -> int:
        """Get scaled estimated container vertical padding."""
        return int(5 * self.scale_factor)

    @property
    def est_container_spacing(self) -> int:
        """Get scaled estimated container spacing."""
        return int(5 * self.scale_factor)

    def _timer_clear_cb(self):
        """Clear the last lap sector bar flag"""
        self.show_last_lap_sector_bar = False
        # Momentarily clear the sector bar
        self.sector_bar.set_sector_status(SectorStatusBar.DEFAULT_SECTOR_STATUS)
