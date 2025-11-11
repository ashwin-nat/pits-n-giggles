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

    def update_data(self, actual_data: list[Dict[str, Any]]):
        """Update table rows with lap data (dicts)."""

        lap_data = [
            {
                "lap-number": 1,
                "s1-time-ms": 30000,
                "s2-time-ms": 30000,
                "s3-time-ms": 30000,
                "lap-time-ms": 90000,
            },
            {
                "lap-number": 2,
                "s1-time-ms": 30000,
                "s2-time-ms": 30000,
                "s3-time-ms": 30000,
                "lap-time-ms": 90000,
            },
            {
                "lap-number": 3,
                "s1-time-ms": 30000,
                "s2-time-ms": 30000,
                "s3-time-ms": 30000,
                "lap-time-ms": 90000,
            },
            {
                "lap-number": 4,
                "s1-time-ms": 30000,
                "s2-time-ms": 30000,
                "s3-time-ms": 30000,
                "lap-time-ms": 90000,
            },
            {
                "lap-number": 5,
                "s1-time-ms": 30000,
                "s2-time-ms": 30000,
                "s3-time-ms": 30000,
                "lap-time-ms": 90000,
            }
        ]
        for row, entry in enumerate(lap_data[:5]):
            self.table.setItem(row, 0, QTableWidgetItem(str(entry.get("lap", "-"))))
            self.table.setItem(row, 1, QTableWidgetItem(str(entry.get("s1", "-"))))
            self.table.setItem(row, 2, QTableWidgetItem(str(entry.get("s2", "-"))))
            self.table.setItem(row, 3, QTableWidgetItem(str(entry.get("s3", "-"))))
            self.table.setItem(row, 4, QTableWidgetItem(str(entry.get("laptime", "-"))))
