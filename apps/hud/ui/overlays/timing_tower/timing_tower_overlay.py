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
from typing import Any, Dict, Optional, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QWidget,
                                QFrame, QSizePolicy, QTableWidget, QTableWidgetItem,
                                QHeaderView)

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay

from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TimingTowerOverlay(BaseOverlay):

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool = False):

        # Overlay specific fields
        self.num_adjacent_cars = 2
        # total rows = (num_adjacent_cars * 2) + 1
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        # UI components
        self.header_label: Optional[QLabel] = None
        self.session_info_label: Optional[QLabel] = None
        self.timing_table: Optional[QTableWidget] = None

        # Tyre compound colors
        self.tyre_colors = {
            "SOFT": QColor("#ff0000"),
            "MEDIUM": QColor("#ffff00"),
            "HARD": QColor("#ffffff"),
            "INTERMEDIATE": QColor("#00ff00"),
            "WET": QColor("#0000ff")
        }

        super().__init__("lap_timer", config, logger, locked)
        self._init_cmd_handlers()

    def build_ui(self):
        """Build the timing tower UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Header section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(3)

        # Session type header
        self.header_label = QLabel("TIMING TOWER")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("""
            QLabel {
                background-color: rgba(200, 0, 0, 220);
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
                border-radius: 4px;
            }
        """)

        # Session info (lap count or time remaining)
        self.session_info_label = QLabel("-- / --")
        self.session_info_label.setAlignment(Qt.AlignCenter)
        self.session_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 200);
                color: #00ff00;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                padding: 5px;
                border-radius: 3px;
            }
        """)

        header_layout.addWidget(self.header_label)
        header_layout.addWidget(self.session_info_label)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 15, 200);
                border-radius: 5px;
            }
        """)

        main_layout.addWidget(header_widget)

        # Create timing table
        self.timing_table = QTableWidget(self.total_rows, 5)
        self.timing_table.setHorizontalHeaderLabels(["Pos", "Driver", "Delta", "Tyre", "ERS"])

        # Configure table appearance
        self.timing_table.setShowGrid(False)
        self.timing_table.setAlternatingRowColors(True)
        self.timing_table.setSelectionMode(QTableWidget.NoSelection)
        self.timing_table.setFocusPolicy(Qt.NoFocus)
        self.timing_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.timing_table.verticalHeader().setVisible(False)
        self.timing_table.horizontalHeader().setVisible(False)

        # Disable scrollbars
        self.timing_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timing_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set column widths
        self.timing_table.setColumnWidth(0, 40)   # Position
        self.timing_table.setColumnWidth(1, 140)  # Driver name
        self.timing_table.setColumnWidth(2, 85)   # Delta (increased for 6 chars)
        self.timing_table.setColumnWidth(3, 45)   # Tyre
        self.timing_table.setColumnWidth(4, 55)   # ERS

        # Configure header
        header = self.timing_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setStretchLastSection(False)

        # Set row heights
        for i in range(self.total_rows):
            self.timing_table.setRowHeight(i, 32)

        # Set fixed size for table to fit all rows without resizing issues
        table_width = 40 + 140 + 85 + 45 + 55 + 20  # columns + margins
        table_height = 32 * self.total_rows + 4  # row height * rows + small margin
        self.timing_table.setFixedSize(table_width, table_height)

        # Apply clean styling
        self.timing_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15, 15, 15, 220);
                border: none;
                border-radius: 6px;
                gridline-color: transparent;
            }

            QTableWidget::item {
                color: white;
                padding: 4px 8px;
                border: none;
                background-color: rgba(25, 25, 25, 180);
            }

            QTableWidget::item:alternate {
                background-color: rgba(20, 20, 20, 180);
            }

            QTableWidget::item:hover {
                background-color: rgba(45, 45, 45, 200);
            }
        """)

        main_layout.addWidget(self.timing_table)

        # Set overall styling
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 220);
                border-radius: 8px;
            }
        """)

        self.clear()

    def _create_table_item(self, text: str, alignment: Qt.AlignmentFlag = Qt.AlignCenter,
                          color: Optional[QColor] = None, font_family: str = None,
                          bold: bool = False) -> QTableWidgetItem:
        """Helper to create styled table items"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)

        if color:
            item.setForeground(QBrush(color))

        if font_family or bold:
            font = QFont()
            if font_family:
                font.setFamily(font_family)
            if bold:
                font.setBold(True)
            font.setPointSize(11)
            item.setFont(font)

        return item

    def _update_row(self, row_idx: int, position: int, name: str, delta: Optional[float],
                   tyre: str, ers: float, is_player: bool = False):
        """Update a specific row in the timing table"""

        # Position
        pos_item = self._create_table_item(str(position), Qt.AlignCenter,
                                          QColor("#ddd"), bold=True)
        self.timing_table.setItem(row_idx, 0, pos_item)

        # Driver name
        name_item = self._create_table_item(name, Qt.AlignLeft | Qt.AlignVCenter,
                                           QColor("#ffffff"), bold=True)
        self.timing_table.setItem(row_idx, 1, name_item)

        # Delta
        if delta is not None and delta > 0:
            delta_text = f"{F1Utils.formatFloat(delta/1000, 3)}"
        elif delta == 0 or delta is None:
            delta_text = "--.-"
        else:
            delta_text = f"{delta:.3f}"

        delta_item = self._create_table_item(delta_text, Qt.AlignCenter,
                                            QColor("#00ff99"), font_family="Courier New")
        self.timing_table.setItem(row_idx, 2, delta_item)

        # Tyre compound
        tyre_display = tyre[:1] if tyre else "--"
        tyre_color = self.tyre_colors.get(tyre, QColor("#cccccc"))
        tyre_item = self._create_table_item(tyre_display, Qt.AlignCenter,
                                           tyre_color, bold=True)
        self.timing_table.setItem(row_idx, 3, tyre_item)

        # ERS
        ers_text = f"{F1Utils.formatFloat(ers, precision=0, signed=False)}%"
        ers_item = self._create_table_item(ers_text, Qt.AlignCenter,
                                          QColor("#ffaa00"), bold=True)
        self.timing_table.setItem(row_idx, 4, ers_item)

        # Highlight player row
        if is_player:
            for col in range(5):
                item = self.timing_table.item(row_idx, col)
                if item:
                    item.setBackground(QBrush(QColor(0, 100, 200, 200)))

    def _clear_row(self, row_idx: int):
        """Clear a specific row"""
        self.timing_table.setItem(row_idx, 0, self._create_table_item("--"))
        self.timing_table.setItem(row_idx, 1, self._create_table_item("---", Qt.AlignLeft))
        self.timing_table.setItem(row_idx, 2, self._create_table_item("--.-"))
        self.timing_table.setItem(row_idx, 3, self._create_table_item("--"))
        self.timing_table.setItem(row_idx, 4, self._create_table_item("0%"))

    def _init_cmd_handlers(self):

        @self.on_command("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:

            relevant_rows = self._get_relevant_race_table_rows(data, self.num_adjacent_cars)
            session_type = data.get("event-type", "N/A")

            # Update header with session type
            self.header_label.setText(f"{session_type.upper()}")

            # Update session info (lap or time)
            if session_type == 'None':
                self.header_label.setText("TIMING TOWER")
                self.session_info_label.setText("----")
            elif self._should_show_lap_number(session_type):
                current_lap = data.get("current-lap", 0)
                total_laps = data.get("total-laps", 0)
                self.session_info_label.setText(f"LAP {current_lap} / {total_laps}")
            else:
                time_remaining_sec = data.get("session-time-left", 0)
                minutes = int(time_remaining_sec // 60)
                seconds = int(time_remaining_sec % 60)
                self.session_info_label.setText(f"TIME: {minutes:02d}:{seconds:02d}")

            # Clear all rows first
            for i in range(self.total_rows):
                self._clear_row(i)

            # Populate rows with data
            for idx, row_data in enumerate(relevant_rows):
                if idx < self.total_rows:
                    position = row_data.get("driver-info", {}).get("position", 0)
                    name = row_data.get("driver-info", {}).get("name", "UNKNOWN")
                    is_player = row_data.get("driver-info", {}).get("is-player", False)
                    delta = row_data.get("delta-info", {}).get("delta-to-car-in-front")
                    tyre = row_data.get("tyre-info", {}).get("visual-tyre-compound", "UNKNOWN")
                    ers = row_data.get("ers-info", {}).get("ers-percent-float", 0.0)

                    self._update_row(idx, position, name, delta, tyre, ers, is_player)

    def clear(self):
        """Clear all timing data"""
        self.header_label.setText("TIMING TOWER")
        self.session_info_label.setText("-- / --")

        for i in range(self.total_rows):
            self._clear_row(i)

    def _get_relevant_race_table_rows(self, data, num_adjacent_cars):
        table_entries = data.get("table-entries", [])

        if len(table_entries) == 0:
            # Normal before session start, when no data is available
            return []

        ref_index = self._get_ref_row_index(data)

        if ref_index is None:
            self.logger.warning(f'<<TIMING_TOWER>> Reference index is None!')
            return []

        ref_position = table_entries[ref_index]["driver-info"]["position"]
        total_cars = len(table_entries)
        lower_bound, upper_bound = self._get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

        if lower_bound is None:
            self.logger.warning(f'<<TIMING_TOWER>> Lower bound is None!')
            return []

        # Sort the list by position before computing relevant positions and update rejoin positions
        sorted_table_entries = sorted(table_entries, key=lambda x: x.get("driver-info", {}).get("position", 999))

        lower_index = lower_bound - 1
        result = sorted_table_entries[lower_index:upper_bound] # since upper bound is exclusive
        return result

    def _get_adjacent_positions(self, position, total_cars, num_adjacent_cars):
        if not (1 <= position <= total_cars):
            return None, None

        min_valid_lower_bound = 1
        max_valid_upper_bound = total_cars

        # In time trial, total_cars will be lower than num_adjacent_cars
        if num_adjacent_cars >= total_cars:
            num_adjacent_cars = total_cars
            lower_bound = min_valid_lower_bound
            upper_bound = max_valid_upper_bound
        # GP scenario, lower bound and upper bound are off input position by num_adjacent_cars
        else:
            lower_bound = position - num_adjacent_cars
            upper_bound = position + num_adjacent_cars

        # now correct if lower and upper bounds have become invalid
        if lower_bound < min_valid_lower_bound:
            # lower bound is negative, need to shift the entire window right
            upper_bound += min_valid_lower_bound - lower_bound
            lower_bound = min_valid_lower_bound

        if upper_bound > total_cars:
            # upper bound is greater than limit, need to shift the entire window left
            lower_bound -= upper_bound - total_cars
            upper_bound = max_valid_upper_bound

        return lower_bound, upper_bound

    def _should_show_lap_number(self, session_type: str) -> bool:
        unsupported_session_types = ['Qualifying', 'Practice', 'Shootout']
        return not any(sub in session_type for sub in unsupported_session_types)
