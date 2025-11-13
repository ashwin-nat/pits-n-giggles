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
from PySide6.QtWidgets import (QVBoxLayout, QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from apps.hud.ui.overlays.timing_tower.race_table import RaceTimingTable

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PitRejoinPredictionPage(BasePage):
    """Pit rejoin position prediction page."""

    def __init__(self, parent: QWidget, logger: logging.Logger):
        # Overlay specific fields
        self.num_adjacent_cars = 2
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        # Timing table component (will be initialized after parent init)
        self.timing_table: Optional[RaceTimingTable] = None

        super().__init__(parent, logger, "mfd.pit_rejoin", title="PIT REJOIN PREDICTION")
        self._build_ui()

    def _build_ui(self):
        """Build the timing tower UI"""
        self._configure_main_layout(self.page_layout)

        # Create and attach the timing table
        self.timing_table = RaceTimingTable(
            parent_layout=self.page_layout,
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

    def _apply_overall_style(self) -> None:
        """Apply background and border styling to the main widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 220);
                border-radius: 8px;
            }
        """)

    def update(self, data: Dict[str, Any]) -> None:
        session_type = data["event-type"]
        if not self._is_race_type_session(session_type):
            self.timing_table.show_error("Only supported in Race/Sprint Sessions")
            return

        table_entries = data["table-entries"]
        if not table_entries:
            self.timing_table.clear()
            return

        ref_row = self._get_ref_row(data)
        if not ref_row:
            self.timing_table.show_error("ERROR: Please check the logs")
            return
        ref_index = ref_row["driver-info"]["index"]

        pit_time_loss = data.get("pit-time-loss")
        if not pit_time_loss:
            self.timing_table.show_error("Pit time loss not configured for this track")
            return

        table_entries.sort(key=lambda x: x["driver-info"]["position"])
        updated_entries = self._add_pit_time_loss(table_entries, pit_time_loss, ref_row)
        relevant_rows = self._get_relevant_race_table_rows(updated_entries, ref_index, self.num_adjacent_cars)
        self._insert_relative_deltas_race(relevant_rows, ref_index)

        # Use the timing table's update_data method
        self.timing_table.update_data(relevant_rows, ref_index)

    def _get_relevant_race_table_rows(
        self,
        sorted_table_entries: Dict[str, Any],
        ref_index: int,
        num_adjacent_cars: int
    ) -> List[Dict[str, Any]]:
        ref_row = next(
            (row for row in sorted_table_entries if row["driver-info"]["index"] == ref_index),
            None
        )
        if not ref_row:
            self.logger.warning(f'{self.overlay_id} Reference row is None!')
            return []

        ref_position = ref_row["driver-info"]["position"]
        total_cars = len(sorted_table_entries)
        lower_bound, upper_bound = self._get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

        if lower_bound is None:
            self.logger.warning(f'{self.overlay_id} Lower bound is None!')
            return []

        lower_index = lower_bound - 1
        result = sorted_table_entries[lower_index:upper_bound]

        if total_cars >= 5:
            assert len(result) == 5
        else:
            assert len(result) == total_cars

        return result

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

    def _is_race_type_session(self, session_type: str) -> bool:
        return "Race" in session_type

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
                total_delta = sum(
                    relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                    for j in range(ref_pos, i)
                )
                row["delta-info"]["relative-delta"] = total_delta

    def _add_pit_time_loss(
        self,
        table_entries: List[Dict[str, Any]],
        pit_time_loss: float,
        ref_row: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Estimate where a driver would rejoin after a pit stop and update their deltas accordingly.
        """

        assert ref_row is not None
        assert pit_time_loss is not None

        # Convert pit loss from seconds --> milliseconds for consistent comparison
        pit_time_loss_ms = pit_time_loss * 1000.0

        # Step 1: Compute projected gap to leader after pit
        ref_delta = ref_row["delta-info"]["delta-to-leader"]
        projected_gap = ref_delta + pit_time_loss_ms

        # Step 2: Find rejoin position (where projected gap would place them)
        rejoin_index = len(table_entries) - 1  # assume they rejoin last
        for i, row in enumerate(table_entries):
            if projected_gap < row["delta-info"]["delta-to-leader"]:
                rejoin_index = i - 1
                break

        rejoin_index = max(rejoin_index, 0)

        # Step 3: Update ref driver info
        ref_row["delta-info"]["delta-to-leader"] = projected_gap

        if rejoin_index >= 0:
            front_driver = table_entries[rejoin_index]
            ref_row["delta-info"]["delta-to-car-in-front"] = (
                projected_gap - front_driver["delta-info"]["delta-to-leader"]
            )
        else:
            # Leader case — no car ahead
            ref_row["delta-info"]["delta-to-car-in-front"] = 0

        # Step 4: Remove driver from current position
        table_entries = [r for r in table_entries if r is not ref_row]

        # Step 5: Insert at new position
        table_entries.insert(rejoin_index + 1, ref_row)

        # Step 6: Reassign positions
        for pos, row in enumerate(table_entries, start=1):
            row["driver-info"]["position"] = pos

        # Step 7: Recompute delta-to-car-in-front for consistency
        for i in range(1, len(table_entries)):
            prev = table_entries[i - 1]["delta-info"]["delta-to-leader"]
            curr = table_entries[i]["delta-info"]["delta-to-leader"]
            table_entries[i]["delta-info"]["delta-to-car-in-front"] = curr - prev

        return table_entries
