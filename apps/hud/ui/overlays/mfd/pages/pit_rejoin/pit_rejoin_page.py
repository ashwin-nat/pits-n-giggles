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
from PySide6.QtWidgets import QVBoxLayout, QWidget

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session)
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
        """Update the page with new data.

        Args:
            data (Dict[str, Any]): The incoming data from the server (top level, including all keys)
        """
        session_type = data["event-type"]
        if not is_race_type_session(session_type):
            self.timing_table.show_error("Only supported in Race/Sprint Sessions")
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
        updated_entries = self._add_pit_time_loss(table_entries, pit_time_loss, ref_row)
        relevant_rows = get_relevant_race_table_rows(updated_entries, self.num_adjacent_cars, ref_index)
        insert_relative_deltas_race(relevant_rows, ref_index)

        # Use the timing table's update_data method
        self.timing_table.update_data(relevant_rows, ref_index)

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
