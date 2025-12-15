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
from enum import Enum
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHeaderView, QSizePolicy, QTableWidget,
                               QTableWidgetItem, QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

from .text_cell_delegate import NoElideDelegate

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class CellColour(Enum):
    NONE = 0
    RED = 1
    GREEN = 2
    PURPLE = 3

class LapTimesPage(BasePage):
    """Lap Times MFD Page."""
    KEY = "lap_times"
    HEADERS = ["Lap", "S1", "S2", "S3", "Time"]
    NUM_ROWS = 5

    LAP_VALID_MASK = 1
    S1_VALID_MASK = 2
    S2_VALID_MASK = 4
    S3_VALID_MASK = 8
    FONT_SIZE = 12
    FONT_FAMILY = "Formula1"
    BASE_ROW_HEIGHT = 40
    BASE_HEADER_HEIGHT = 35
    BASE_PADDING = 4

    def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
        """Initialize lap times page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
            scale_factor (float): Scale factor
        """
        self.scale_factor = scale_factor
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="RECENT LAP TIMES")
        self._last_processed_data: List[Dict[str, Any]] = []

        self.table = QTableWidget(self.NUM_ROWS, len(self.HEADERS), self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.verticalHeader().setVisible(False)

        # Disable mouse interaction
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Make table transparent to mouse events so parent can handle dragging
        self.table.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Hide scroll bars
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Styling table appearance
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)

        # Apply font to table
        table_font = QFont(self.FONT_FAMILY, self.font_size)
        self.table.setFont(table_font)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
            }}
            QTableWidget::item {{
                padding: {self.scaled_padding}px;
                font-family: {self.FONT_FAMILY};
                font-size: {self.font_size}pt;
            }}
            QTableWidget::item:alternate {{
                background-color: #252525;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {self.scaled_padding}px;
                border: 1px solid #3a3a3a;
                font-family: {self.FONT_FAMILY};
                font-size: {self.font_size}pt;
                font-weight: bold;
            }}
        """)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(self.scaled_row_height)
        self.table.horizontalHeader().setFixedHeight(self.scaled_header_height)

        # Set size policy to expand and fill
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.table.setItemDelegate(NoElideDelegate(self.table))
        self.page_layout.addWidget(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self._init_event_handlers()

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            """Populate the lap table with up to the last 5 laps. Leave remaining rows blank."""
            lap_time_history = data.get("lap-time-history", {})
            if not lap_time_history:
                return

            if self._last_processed_data == lap_time_history:
                return

            history_data = lap_time_history.get("lap-time-history-data", [])
            if not history_data:
                return

            # Get the last 5 laps (if fewer exist, it's fine)
            recent_laps = history_data[-self.NUM_ROWS:]
            if not recent_laps:
                return

            # Clear old contents but keep headers
            self.table.clearContents()

            pb_lap_num = lap_time_history["fastest-lap-number"]
            pb_s1_lap_num = lap_time_history["fastest-s1-lap-number"]
            pb_s2_lap_num = lap_time_history["fastest-s2-lap-number"]
            pb_s3_lap_num = lap_time_history["fastest-s3-lap-number"]
            glob_best_lap_ms = lap_time_history["global-fastest-lap-ms"]
            glob_best_s1_ms = lap_time_history["global-fastest-s1-ms"]
            glob_best_s2_ms = lap_time_history["global-fastest-s2-ms"]
            glob_best_s3_ms = lap_time_history["global-fastest-s3-ms"]

            # Fill available laps (latest at bottom)
            for row, lap_info in enumerate(reversed(recent_laps)):
                lap_num = lap_info["lap-number"]
                s1_time_ms  = lap_info["sector-1-time-in-ms"]
                s2_time_ms  = lap_info["sector-2-time-in-ms"]
                s3_time_ms  = lap_info["sector-3-time-in-ms"]
                lap_time_ms = lap_info["lap-time-in-ms"]

                s1_time_str = lap_info["sector-1-time-str"]
                s2_time_str = lap_info["sector-2-time-str"]
                s3_time_str = lap_info["sector-3-time-str"]
                lap_time_str= lap_info["lap-time-str"]
                validFlags = lap_info["lap-valid-bit-flags"]

                # Determine validity for each sector and lap
                s1_valid = bool(validFlags & self.S1_VALID_MASK)
                s2_valid = bool(validFlags & self.S2_VALID_MASK)
                s3_valid = bool(validFlags & self.S3_VALID_MASK)
                lap_valid = bool(validFlags & self.LAP_VALID_MASK)

                # Create data tuples: (value, time_ms, pb_lap_num, global_best_ms, is_valid)
                cell_data = [
                    (lap_num, None, None, None, True),
                    (s1_time_str, s1_time_ms, pb_s1_lap_num, glob_best_s1_ms, s1_valid),
                    (s2_time_str, s2_time_ms, pb_s2_lap_num, glob_best_s2_ms, s2_valid),
                    (s3_time_str, s3_time_ms, pb_s3_lap_num, glob_best_s3_ms, s3_valid),
                    (lap_time_str, lap_time_ms, pb_lap_num, glob_best_lap_ms, lap_valid)
                ]

                for col, (value, time_ms, pb_lap, global_best, is_valid) in enumerate(cell_data):
                    if col == 0:
                        content = str(value)
                    else:
                        content = value if value not in ["0.000", "00:00.000"] else "---"

                    item = QTableWidgetItem(content)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Apply color if not lap number column
                    if col > 0:
                        cell_color = self._get_cell_text_colour(lap_num, time_ms, global_best, pb_lap, is_valid)
                        if cell_color == CellColour.PURPLE:
                            item.setForeground(Qt.GlobalColor.magenta)
                        elif cell_color == CellColour.GREEN:
                            item.setForeground(Qt.GlobalColor.green)
                        elif cell_color == CellColour.RED:
                            item.setForeground(Qt.GlobalColor.red)

                    self.table.setItem(row, col, item)

            # Update the cache
            self._last_processed_data = lap_time_history

    def _get_cell_text_colour(self, lap_num: int, time_ms: int, global_best_time_ms: int,
                              pb_lap_num: int, isValid: bool) -> CellColour:
        """Get the text colour for a cell"""
        if global_best_time_ms and (time_ms == global_best_time_ms):
            return CellColour.PURPLE
        if pb_lap_num and (lap_num == pb_lap_num):
            return CellColour.GREEN
        if not isValid:
            return CellColour.RED
        return CellColour.NONE

    @property
    def font_size(self) -> int:
        """Get the font size based on the scale factor."""
        return int(self.FONT_SIZE * self.scale_factor)

    @property
    def scaled_row_height(self) -> int:
        """Get the scaled row height."""
        return int(self.BASE_ROW_HEIGHT * self.scale_factor)

    @property
    def scaled_header_height(self) -> int:
        """Get the scaled header height."""
        return int(self.BASE_HEADER_HEIGHT * self.scale_factor)

    @property
    def scaled_padding(self) -> int:
        """Get the scaled padding."""
        return int(self.BASE_PADDING * self.scale_factor)
