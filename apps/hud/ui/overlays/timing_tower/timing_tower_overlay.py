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
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session,
                             is_tt_session)
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay

from .race_table import RaceTimingTable

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TimingTowerOverlay(BaseOverlay):

    OVERLAY_ID: str = "timing_tower"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int):

        # Overlay specific fields
        self.num_adjacent_cars = 2
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        # UI components
        self.header_label: Optional[QLabel] = None
        self.session_info_label: Optional[QLabel] = None
        self.timing_table: Optional[RaceTimingTable] = None

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity)
        self._init_cmd_handlers()

    def build_ui(self):
        """Build the timing tower UI"""
        main_layout = QVBoxLayout(self)
        self._configure_main_layout(main_layout)

        content_width = self._calculate_content_width()

        header_widget = self._create_header_section(content_width)
        main_layout.addWidget(header_widget)

        # Create and attach the timing table
        self.timing_table = RaceTimingTable(
            parent_layout=main_layout,
            logger=self.logger,
            overlay_id=self.overlay_id,
            num_rows=self.total_rows
        )

        self._apply_overall_style()

    def _configure_main_layout(self, layout: QVBoxLayout) -> None:
        """Configure main layout spacing, margins, and alignment."""
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _calculate_content_width(self) -> int:
        """Return total content width based on column sizes."""
        return 40 + 30 + 160 + 90 + 75 + 75 + 50

    def _create_header_section(self, content_width: int) -> QWidget:
        """Create the header section with title and session info."""
        header_widget = QWidget()
        header_widget.setFixedWidth(content_width)

        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 5, 0, 5)
        header_layout.setSpacing(3)

        self.header_label = QLabel("TIMING TOWER")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        self.session_info_label = QLabel("-- / --")
        self.session_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        return header_widget

    def _apply_overall_style(self) -> None:
        """Apply background and border styling to the main widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 220);
                border-radius: 8px;
            }
        """)

    def _init_cmd_handlers(self):

        @self.on_command("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:

            session_type = data["event-type"]
            if is_tt_session(session_type):
                self.header_label.setText("TIME TRIAL")
                self.session_info_label.setText("-- / --")
                self.timing_table.show_error("TIME TRIAL NOT YET SUPPORTED")
                return

            table_entries = data["table-entries"]
            if not table_entries:
                self.timing_table.clear()
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                self.timing_table.show_error("ERROR: Please check the logs")
                return
            ref_index = ref_row["driver-info"]["index"]

            pit_time_loss = data.get("pit-time-loss")
            if not pit_time_loss:
                self.timing_table.show_error("Pit time loss not configured for this track")
                return

            table_entries.sort(key=lambda x: x["driver-info"]["position"])
            relevant_rows = get_relevant_race_table_rows(table_entries, self.num_adjacent_cars, ref_index)
            if is_race_type_session(session_type):
                insert_relative_deltas_race(relevant_rows, ref_index)
            elif not is_tt_session(session_type):
                self._insert_relative_deltas_fp_quali(relevant_rows, ref_row)

            # Use the timing table's update_data method
            self.timing_table.update_data(relevant_rows, ref_index)

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

    def clear(self):
        """Clear all timing data"""
        self.header_label.setText("TIMING TOWER")
        self.session_info_label.setText("-- / --")
        self.timing_table.clear()

    def _should_show_lap_number(self, session_type: str) -> bool:
        return is_race_type_session(session_type)

    def _insert_relative_deltas_fp_quali(self, relevant_rows: List[Dict[str, Any]], ref_row: Dict[str, Any]) -> None:
        """Insert relative deltas for FP/Quali mode

        Args:
            relevant_rows (List[Dict[str, Any]]): List of relevant rows
            ref_row (Dict[str, Any]): The reference row
        """
        if not ref_row:
            self.logger.warning('<<TIMING_TOWER>> Reference row is None!')
            return
        ref_best_lap_ms = ref_row["lap-info"]["best-lap"]["lap-time-ms"]

        # For each car, compute the best lap delta against the ref car
        # ref lap - car lap
        for row in relevant_rows:
            best_lap_ms = row["lap-info"]["best-lap"]["lap-time-ms"]
            if ref_best_lap_ms is None or best_lap_ms is None:
                row["delta-info"]["relative-delta"] = 0
            else:
                row["delta-info"]["relative-delta"] = best_lap_ms - ref_best_lap_ms
