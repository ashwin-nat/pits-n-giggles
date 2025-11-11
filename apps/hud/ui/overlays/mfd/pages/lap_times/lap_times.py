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
import itertools
from typing import Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapTimesPage(QWidget):
    """Simple 5x5 table for lap times."""

    HEADERS = ["Lap", "S1", "S2", "S3", "Lap Time"]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(5, 5, self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        layout.addWidget(self.table)

    def update_data(self, actual_data: Dict[str, Any]):
        """Populate the lap table with up to the last 5 laps. Leave remaining rows blank."""
        lap_time_history = actual_data.get("lap-time-history", {})
        if not lap_time_history:
            return

        history_data = lap_time_history.get("lap-time-history-data", [])
        if not history_data:
            return

        # Get the last 5 laps (if fewer exist, it’s fine)
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
