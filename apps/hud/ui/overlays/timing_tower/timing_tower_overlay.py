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
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QWidget,
                                QFrame, QSizePolicy)

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay

from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TimingTowerRow(QWidget):
    """Individual row in the timing tower"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Position label (narrow)
        self.pos_label = QLabel("--")
        self.pos_label.setFixedWidth(30)
        self.pos_label.setAlignment(Qt.AlignCenter)
        self.pos_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 200);
                color: white;
                font-weight: bold;
                border-radius: 3px;
                padding: 2px;
            }
        """)

        # Driver name (expandable)
        self.name_label = QLabel("---")
        self.name_label.setMinimumWidth(120)
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                padding-left: 5px;
            }
        """)

        # Delta (fixed width)
        self.delta_label = QLabel("--.-")
        self.delta_label.setFixedWidth(60)
        self.delta_label.setAlignment(Qt.AlignCenter)
        self.delta_label.setStyleSheet("""
            QLabel {
                background-color: rgba(60, 60, 60, 200);
                color: #00ff00;
                font-family: 'Courier New', monospace;
                border-radius: 3px;
                padding: 2px;
            }
        """)

        # Tyre compound (narrow)
        self.tyre_label = QLabel("--")
        self.tyre_label.setFixedWidth(35)
        self.tyre_label.setAlignment(Qt.AlignCenter)
        self.tyre_label.setStyleSheet("""
            QLabel {
                background-color: rgba(50, 50, 50, 200);
                color: white;
                font-weight: bold;
                border-radius: 3px;
                padding: 2px;
            }
        """)

        # ERS bar/indicator (fixed width)
        self.ers_label = QLabel("0%")
        self.ers_label.setFixedWidth(45)
        self.ers_label.setAlignment(Qt.AlignCenter)
        self.ers_label.setStyleSheet("""
            QLabel {
                background-color: rgba(50, 50, 50, 200);
                color: #ffaa00;
                font-weight: bold;
                border-radius: 3px;
                padding: 2px;
            }
        """)

        layout.addWidget(self.pos_label)
        layout.addWidget(self.name_label, 1)  # Stretch factor 1
        layout.addWidget(self.delta_label)
        layout.addWidget(self.tyre_label)
        layout.addWidget(self.ers_label)

        # Row background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 180);
                border: 1px solid rgba(80, 80, 80, 150);
                border-radius: 4px;
            }
        """)

    def update_data(self, position: int, name: str, delta: Optional[float],
                    tyre: str, ers: float, is_player: bool = False):
        """Update row with race data"""
        self.pos_label.setText(str(position))
        self.name_label.setText(name)

        # Format delta
        if delta is not None and delta > 0:
            self.delta_label.setText(f"{F1Utils.formatFloat(delta/1000, 3)}")
        elif delta == 0 or delta is None:
            self.delta_label.setText("--.-")
        else:
            self.delta_label.setText(f"{delta:.3f}")

        # Tyre compound colors
        tyre_colors = {
            "SOFT": "#ff0000",
            "MEDIUM": "#ffff00",
            "HARD": "#ffffff",
            "INTERMEDIATE": "#00ff00",
            "WET": "#0000ff"
        }
        tyre_display = tyre[:1] if tyre else "--"
        self.tyre_label.setText(tyre_display)
        if tyre in tyre_colors:
            self.tyre_label.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(50, 50, 50, 200);
                    color: {tyre_colors[tyre]};
                    font-weight: bold;
                    border-radius: 3px;
                    padding: 2px;
                }}
            """)

        # ERS percentage
        self.ers_label.setText(f"{F1Utils.formatFloat(ers, precision=0, signed=False)}%")

        # Highlight player row
        if is_player:
            self.setStyleSheet("""
                QWidget {
                    background-color: rgba(0, 100, 200, 200);
                    border: 2px solid rgba(0, 150, 255, 255);
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: rgba(20, 20, 20, 180);
                    border: 1px solid rgba(80, 80, 80, 150);
                    border-radius: 4px;
                }
            """)

    def clear(self):
        """Clear row data"""
        self.pos_label.setText("--")
        self.name_label.setText("---")
        self.delta_label.setText("--.-")
        self.tyre_label.setText("--")
        self.ers_label.setText("0%")


class TimingTowerOverlay(BaseOverlay):

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool = False):

        # Overlay specific fields
        self.num_adjacent_cars = 2
        # total rows = (num_adjacent_cars * 2) + 1
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        # UI components
        self.header_label: Optional[QLabel] = None
        self.session_info_label: Optional[QLabel] = None
        self.timing_rows: List[TimingTowerRow] = []

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

        # Timing rows
        for i in range(self.total_rows):
            row = TimingTowerRow(self)
            self.timing_rows.append(row)
            main_layout.addWidget(row)

        # Add stretch at bottom
        main_layout.addStretch()

        # Set overall styling
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 220);
                border-radius: 8px;
            }
        """)

    def _init_cmd_handlers(self):

        @self.on_command("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:

            relevant_rows = self._get_relevant_race_table_rows(data, self.num_adjacent_cars)
            session_type = data.get("event-type", "N/A")

            # Update header with session type
            self.header_label.setText(f"{session_type.upper()}")

            # Update session info (lap or time)
            if self._should_show_lap_number(session_type):
                current_lap = data.get("current-lap", 0)
                total_laps = data.get("total-laps", 0)
                self.session_info_label.setText(f"LAP {current_lap} / {total_laps}")
            else:
                time_remaining_sec = data.get("session-time-left", 0)
                minutes = int(time_remaining_sec // 60)
                seconds = int(time_remaining_sec % 60)
                self.session_info_label.setText(f"TIME: {minutes:02d}:{seconds:02d}")

            # Clear all rows first
            for row in self.timing_rows:
                row.clear()
                row.hide()

            # Populate rows with data
            for idx, row_data in enumerate(relevant_rows):
                if idx < len(self.timing_rows):
                    timing_row = self.timing_rows[idx]


                    position = row_data.get("driver-info", {}).get("position", 0)
                    name = row_data.get("driver-info", {}).get("name", "UNKNOWN")
                    is_player = row_data.get("driver-info", {}).get("is-player", False)
                    delta = row_data.get("delta-info", {}).get("delta-to-car-in-front")
                    tyre = row_data.get("tyre-info", {}).get("visual-tyre-compound", "UNKNOWN")
                    ers = row_data.get("ers-info", {}).get("ers-percent-float", 0.0)


                    timing_row.update_data(position, name, delta, tyre, ers, is_player)
                    timing_row.show()

    def clear(self):
        """Clear all timing data"""
        self.header_label.setText("TIMING TOWER")
        self.session_info_label.setText("-- / --")

        for row in self.timing_rows:
            row.clear()
            row.hide()

    def _get_relevant_race_table_rows(self, data, num_adjacent_cars):
        table_entries = data.get("table-entries", [])

        if len(table_entries) == 0:
            # Normal before session start, when no data is available
            return []

        # Sort the list by position before computing relevant positions and update rejoin positions
        sorted_table_entries = sorted(table_entries, key=lambda x: x.get("driver-info", {}).get("position", 999))
        total_cars = len(sorted_table_entries)

        ref_index = self._get_ref_row_index(data)

        if ref_index is None:
            self.logger.warning(f'<<TIMING_TOWER>> Reference index is None!')
            return []

        ref_position = sorted_table_entries[ref_index]["driver-info"]["position"]
        lower_bound, upper_bound = self._get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

        if lower_bound is None:
            self.logger.warning(f'<<TIMING_TOWER>> Lower bound is None!')
            return []

        result = sorted_table_entries[lower_bound:upper_bound]
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
        unsupported_session_types = ['Qualifying', 'Practice', 'Sprint Shootout']
        return session_type not in unsupported_session_types
