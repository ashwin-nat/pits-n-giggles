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
from typing import Any, Dict, Optional, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

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
            icon_loader=self.load_icon,
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
            relevant_rows, ref_index = self._get_relevant_race_table_rows(data, self.num_adjacent_cars)

            if self._is_race_type_session(session_type):
                self._insert_relative_deltas_race(relevant_rows, ref_index)
            elif not self._is_tt_session(session_type):
                self._insert_relative_deltas_fp_quali(relevant_rows, ref_index)

            session_type: str = data.get("event-type", "N/A")

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

            # Use the timing table's update_data method
            self.timing_table.update_data(relevant_rows, ref_index)

    def clear(self):
        """Clear all timing data"""
        self.header_label.setText("TIMING TOWER")
        self.session_info_label.setText("-- / --")
        self.timing_table.clear()

    def _get_relevant_race_table_rows(
        self,
        data: Dict[str, Any],
        num_adjacent_cars: int
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        table_entries = data.get("table-entries", [])

        if len(table_entries) == 0:
            # Normal before session start, when no data is available
            return [], None

        ref_index = self._get_ref_row_index(data)

        if ref_index is None:
            self.logger.warning('<<TIMING_TOWER>> Reference index is None!')
            return [], None

        ref_position = table_entries[ref_index]["driver-info"]["position"]
        total_cars = len(table_entries)
        lower_bound, upper_bound = self._get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

        if lower_bound is None:
            self.logger.warning('<<TIMING_TOWER>> Lower bound is None!')
            return [], None

        # Sort the list by position before computing relevant positions and update rejoin positions
        sorted_table_entries = sorted(table_entries, key=lambda x: x.get("driver-info", {}).get("position", 999))

        lower_index = lower_bound - 1
        result = sorted_table_entries[lower_index:upper_bound] # since upper bound is exclusive

        if total_cars >= 5:
            assert len(result) == 5
        else:
            assert len(result) == total_cars

        return result, ref_index

    def _get_adjacent_positions(self, position, total_cars, num_adjacent_cars):
        if not (1 <= position <= total_cars):
            return None, None

        min_valid_lower_bound = 1
        max_valid_upper_bound = total_cars

        # Calculate a window of num_adjacent_cars on each side of the position (inclusive bounds).
        # If the window exceeds valid bounds, shift it towards the center while capping at boundaries
        # to ensure lower_bound stays >= 1 and upper_bound stays <= total_cars.
        lower_bound = position - num_adjacent_cars
        upper_bound = position + num_adjacent_cars

        # Adjust if window exceeds boundaries
        if lower_bound < min_valid_lower_bound:
            shift = min_valid_lower_bound - lower_bound
            lower_bound = min_valid_lower_bound
            upper_bound = min(upper_bound + shift, max_valid_upper_bound)

        if upper_bound > max_valid_upper_bound:
            shift = upper_bound - max_valid_upper_bound
            upper_bound = max_valid_upper_bound
            lower_bound = max(lower_bound - shift, min_valid_lower_bound)

        return lower_bound, upper_bound

    def _is_tt_session(self, session_type: str) -> bool:
        return session_type == "Time Trial"

    def _is_race_type_session(self, session_type: str) -> bool:
        return "Race" in session_type

    def _should_show_lap_number(self, session_type: str) -> bool:
        unsupported_session_types = ['Qualifying', 'Practice', 'Shootout']
        return not any(sub in session_type for sub in unsupported_session_types)

    def _insert_relative_deltas_race(self, relevant_rows, ref_index) -> None:
        if ref_index is None:
            return

        # Map driver index --> position in relevant_rows
        index_to_pos = {
            row["driver-info"]["index"]: i for i, row in enumerate(relevant_rows)
        }

        ref_pos = index_to_pos.get(ref_index)
        if ref_pos is None:
            return

        # For each car, sum the deltas between it and the reference car;
        # cars ahead get negative values, cars behind get positive values.
        for i, row in enumerate(relevant_rows):
            if i == ref_pos:
                row["delta-info"]["relative-delta"] = 0
                continue

            if i < ref_pos:
                # Car(s) ahead of reference
                total_delta = sum(
                    relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                    for j in range(i, ref_pos)
                )
                row["delta-info"]["relative-delta"] = -total_delta
            else:
                # Car(s) behind reference
                total_delta = sum(
                    relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                    for j in range(ref_pos, i)
                )
                row["delta-info"]["relative-delta"] = total_delta

    def _insert_relative_deltas_fp_quali(self, relevant_rows, ref_index) -> None:
        if ref_index is None:
            return

        ref_row = next(
            (
                row
                for row in relevant_rows
                if row["driver-info"]["index"] == ref_index
            ),
            None
        )
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
