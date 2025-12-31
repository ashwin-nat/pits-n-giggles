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
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

from PySide6.QtQuick import QQuickItem

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session)
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.f1_types import F1Utils

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PitRejoinPredictionPage(MfdPageBase):
    """Pit rejoin position prediction page."""
    KEY = "pit_rejoin"
    QML_FILE: Path = Path(__file__).parent / "pit_rejoin_page.qml"

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        super().__init__(overlay, logger)
        self._init_event_handlers()

        self.num_adjacent_cars = 2
        self.total_rows = (self.num_adjacent_cars * 2) + 1

    def _init_event_handlers(self):
        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            """Update the page with new data.

            Args:
                data (Dict[str, Any]): The incoming data from the server (top level, including all keys)
            """
            page_item = self._page_item
            if not page_item:
                return

            session_type = data["event-type"]
            if not is_race_type_session(session_type):
                self._show_empty_table(page_item)
                return

            table_entries = data["table-entries"]
            if not table_entries:
                self._show_empty_table(page_item)
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                self._show_empty_table(page_item)
                return
            ref_index = ref_row["driver-info"]["index"]

            pit_time_loss = data.get("pit-time-loss")
            if not pit_time_loss:
                self._show_empty_table(page_item)
                return

            # Update pit time loss header
            pit_time_loss_str = f"Pit Time Loss: {pit_time_loss:.1f}s"

            table_entries.sort(key=lambda x: x["driver-info"]["position"])
            updated_entries = self._add_pit_time_loss(table_entries, pit_time_loss, ref_row)
            relevant_rows = get_relevant_race_table_rows(updated_entries, self.num_adjacent_cars, ref_index)
            insert_relative_deltas_race(relevant_rows, ref_index)

            # Update the table
            self._update_table(pit_time_loss_str, relevant_rows, ref_index, page_item)

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
            # Leader case - no car ahead
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

    def _show_empty_table(self, page_item: QQuickItem):
        """Display empty table."""
        page_item.showEmptyTable()

    def _update_table(self, pit_time_loss_str: str, relevant_rows: List[Dict[str, Any]], ref_index: int, page_item: QQuickItem):
        """Update the table with new data.

        Args:
            pit_time_loss_str (str): Formatted pit time loss string
            relevant_rows (List[Dict[str, Any]]): List of row data dictionaries
            ref_index (int): Reference driver index
            page_item (QQuickItem): Page item
        """

        # Convert rows to QML-friendly format
        rows_data = []
        for row_data in relevant_rows:
            driver_info: Dict[str, Any] = row_data.get("driver-info", {})
            delta_info: Dict[str, Any] = row_data.get("delta-info", {})
            tyre_info: Dict[str, Any] = row_data.get("tyre-info", {})

            position = driver_info.get("position", 0)
            team = driver_info.get("team", "")
            name = driver_info.get("name", "")
            delta_value = delta_info.get("relative-delta", 0.0)
            driver_idx = driver_info.get("index", -1)
            is_ref = (driver_idx == ref_index)

            # Format delta
            if is_ref:
                delta_str = '---'
                delta_color = "white"
            else:
                delta_str = F1Utils.formatFloat(delta_value / 1000, precision=3, signed=True)
                # Color based on delta (green for negative/ahead, red for positive/behind)
                if delta_value < 0:
                    delta_color = "#00FF00"  # Green
                elif delta_value > 0:
                    delta_color = "#FF0000"  # Red
                else:
                    delta_color = "white"

            compound = tyre_info.get("visual-tyre-compound", "")
            tyre_age = tyre_info.get("tyre-age", 0)

            rows_data.append({
                "position": str(position),
                "team": team,
                "name": name,
                "delta": delta_str,
                "deltaColor": delta_color,
                "isRef": is_ref,
                "compound": compound,
                "tyreAge": f"{tyre_age}L",
            })

        # Call QML function to update
        page_item.updateData(pit_time_loss_str, rows_data, ref_index)
