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

import itertools
import logging
from typing import Any, Dict

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHeaderView, QLabel, QStackedWidget,
                               QStyledItemDelegate, QTableWidget, QStyleOptionViewItem,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class NoElideDelegate(QStyledItemDelegate):
    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        # prepare the option as usual
        super().initStyleOption(option, index)
        # set the elide mode on the style option so Qt won't draw "…"
        # new enum location may vary between PySide6 versions, so try both
        option.textElideMode = Qt.TextElideMode.ElideNone

class LapTimesPage(BasePage):
    """Elegant lap times table with modern styling."""
    HEADERS = ["Lap", "S1", "S2", "S3", "Lap Time"]

    def __init__(self, parent: QWidget, logger: logging.Logger):

        self.overlay_id: str = "mfd.lap_times"
        super().__init__(parent, logger, "RECENT LAP TIMES")

        # Font configuration
        FONT_SIZE = 9
        FONT_FAMILY = "Montserrat"  # Clean, modern font (falls back gracefully)
        HEADER_FONT = "Montserrat"  # F1-style font (you can change this to any other appropriate font)
        HEADER_FONT_SIZE = 9

        self.table = QTableWidget(5, 5, self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Disable mouse interaction
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Hide scroll bars
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Styling table appearance
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)

        # Apply font to table
        table_font = QFont(FONT_FAMILY, FONT_SIZE)
        self.table.setFont(table_font)

        # Cleaned-up and fixed stylesheet
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3a3a3a;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }}
            QTableWidget::item {{
                padding: 2px;
                font-family: {FONT_FAMILY};
                font-size: {FONT_SIZE}pt;
            }}
            QTableWidget::item:alternate {{
                background-color: #252525;
            }}
            QHeaderView::section {{
                background-color: #2d2d2d;
                color: #FF0000;  /* Red text for headers */
                padding: 8px;
                border: none;
                border-bottom: 2px solid #FF0000;  /* Red bottom border */
                font-weight: bold;
                font-family: {HEADER_FONT};
                font-size: {HEADER_FONT_SIZE}pt;
            }}
        """)

        # Set column widths here (adjust as needed)
        self.table.setColumnWidth(0, 20)  # Set width for the "Lap" column (index 0)
        self.table.setColumnWidth(1, 100) # Set width for the "S1" column (index 1)
        self.table.setColumnWidth(2, 100) # Set width for the "S2" column (index 2)
        self.table.setColumnWidth(3, 100) # Set width for the "S3" column (index 3)
        self.table.setColumnWidth(4, 150) # Set width for the "Lap Time" column (index 4)

        # Disable text ellipsis — text will just be truncated visually
        self.table.setItemDelegate(NoElideDelegate(self.table))
        self.page_layout.addWidget(self.table)

    def update_data(self, actual_data: Dict[str, Any]):
        """Populate the lap table with up to the last 5 laps. Leave remaining rows blank."""
        lap_time_history = actual_data.get("lap-time-history", {})
        if not lap_time_history:
            return

        history_data = lap_time_history.get("lap-time-history-data", [])
        if not history_data:
            return

        # Get the last 5 laps (if fewer exist, it's fine)
        recent_laps = history_data[-5:]

        # Clear old contents but keep headers
        self.table.clearContents()

        # Fill available laps (latest at bottom)
        for row, lap_info in enumerate(reversed(recent_laps)):
            lap_num = lap_info.get("lap-number", "-")
            s1_time = lap_info.get("sector-1-time-str", "-")
            s2_time = lap_info.get("sector-2-time-str", "-")
            s3_time = lap_info.get("sector-3-time-str", "-")
            lap_time = lap_info.get("lap-time-str", "-")

            for col, value in enumerate([lap_num, s1_time, s2_time, s3_time, lap_time]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
