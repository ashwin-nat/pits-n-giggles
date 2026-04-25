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
from lib.config import MfdPageId
from lib.f1_types import F1Utils

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PitRejoinPredictionPage(MfdPageBase):
    """Pit rejoin position prediction page."""
    KEY = MfdPageId.PIT_REJOIN
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

            # Compute how much pit time the ref car has already served (0 if not yet in pits).
            # Guard with pit-lane-timer-active so we don't accidentally use a stale timer
            # value from the previous stint.
            ref_pit_info = ref_row.get("pit-info", {})
            pit_lane_timer_active = ref_pit_info.get("pit-lane-timer-active", False)
            time_already_in_pit_ms = (
                ref_pit_info.get("pit-lane-timer-ms", 0) if pit_lane_timer_active else 0
            )

            # Update pit time loss header
            pit_time_loss_str = f"Pit Time Loss: {pit_time_loss:.1f}s"

            updated_entries = self._add_pit_time_loss(
                table_entries, pit_time_loss, ref_row, time_already_in_pit_ms
            )
            relevant_rows = get_relevant_race_table_rows(updated_entries, self.num_adjacent_cars, ref_index)
            insert_relative_deltas_race(relevant_rows, ref_index)

            # Update the table
            self._update_table(pit_time_loss_str, relevant_rows, ref_index, page_item)

    def _get_rival_effective_delta(self, row: Dict[str, Any], pit_time_loss_ms: float) -> float:
        """Return a rival's effective delta-to-leader, adjusted if they are currently in the pit lane.

        A rival's stored delta is a snapshot from when their data was last updated. If they are
        mid-pit, their real gap is growing. We estimate their gap at pit exit by adding their
        remaining pit time loss.

        Example: rival is 5 s behind with 8 s of a 20 s pit already served.
            remaining = 12 s  ->  effective delta = 17 s.

        Args:
            row: Rival's race table row.
            pit_time_loss_ms: Total expected pit time loss in milliseconds.

        Returns:
            Effective delta-to-leader in milliseconds.
        """
        pit_info = row.get("pit-info", {})
        raw_delta = row["delta-info"]["delta-to-leader"]

        if not pit_info.get("pit-lane-timer-active", False):
            return raw_delta

        time_spent_ms = pit_info.get("pit-lane-timer-ms", 0)
        remaining_ms = max(pit_time_loss_ms - time_spent_ms, 0.0)
        return raw_delta + remaining_ms

    def _add_pit_time_loss(
        self,
        table_entries: List[Dict[str, Any]],
        pit_time_loss: float,
        ref_row: Dict[str, Any],
        time_already_in_pit_ms: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Estimate where the ref driver rejoins after a pit stop.

        Handles two pit-adjusted scenarios:

        1. Ref on track, rival pitting: rival's effective delta is inflated by their remaining
           pit time so they are correctly slotted behind their exit position, not their stale
           on-track position.

        2. Ref already pitting: only the remaining pit time loss (total - elapsed) is added to
           the ref's projected gap, so the prediction tightens in real time as the ref moves
           through the pit lane.

        DNF / DSQ cars remain in the table but are ignored for all rejoin calculations,
        since their deltas are stale.

        Args:
            table_entries (List[Dict[str, Any]]): Full race table.
            pit_time_loss (float): Total expected pit time loss in seconds.
            ref_row (Dict[str, Any]): Reference (POV) driver row.
            time_already_in_pit_ms (float): Milliseconds the ref car has already spent in the
                pit lane this stop. Defaults to 0 (not yet in pits).

        Returns:
            List[Dict[str, Any]]: Updated table entries with the ref driver repositioned.
        """

        assert ref_row is not None
        assert pit_time_loss is not None

        # Convert pit loss from seconds --> milliseconds for consistent comparison
        pit_time_loss_ms = pit_time_loss * 1000.0

        # Remaining time the ref car still has to spend in the pits.
        # Clamped to 0 so we never project a negative (beneficial) pit stop.
        remaining_pit_loss_ms = max(pit_time_loss_ms - time_already_in_pit_ms, 0.0)

        # Step 1: Compute projected gap to leader after pit using only the *remaining* loss
        ref_delta = ref_row["delta-info"]["delta-to-leader"]
        projected_gap = ref_delta + remaining_pit_loss_ms

        # Step 2: Determine rejoin index while SKIPPING DNF / DSQ cars
        rejoin_index = None
        last_active_index = None

        for i, row in enumerate(table_entries):
            if not self._is_active_car(row) or row is ref_row:
                continue

            last_active_index = i

            rival_effective_delta = self._get_rival_effective_delta(row, pit_time_loss_ms)
            if projected_gap < rival_effective_delta:
                rejoin_index = max(i - 1, 0)
                break

        if rejoin_index is None:
            # Rejoin after the last active car
            rejoin_index = last_active_index if last_active_index is not None else 0

        # Step 3: Update ref deltas
        ref_row["delta-info"]["delta-to-leader"] = projected_gap

        # Find the nearest ACTIVE car in front
        front_driver = None
        for i in range(rejoin_index, -1, -1):
            candidate = table_entries[i]
            if candidate is not ref_row and self._is_active_car(candidate):
                front_driver = candidate
                break

        if front_driver:
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

        # Step 6: Reassign positions (DNF / DSQ included)
        for pos, row in enumerate(table_entries, start=1):
            row["driver-info"]["position"] = pos

        # Step 7: Recompute delta-to-car-in-front, skipping inactive cars when looking "forward"
        last_active_row = None
        for row in table_entries:
            if not self._is_active_car(row):
                continue

            if last_active_row is None:
                row["delta-info"]["delta-to-car-in-front"] = 0
            else:
                row["delta-info"]["delta-to-car-in-front"] = (
                    row["delta-info"]["delta-to-leader"]
                    - last_active_row["delta-info"]["delta-to-leader"]
                )

            last_active_row = row

        return table_entries

    def _show_empty_table(self, page_item: QQuickItem):
        """Display empty table."""
        page_item.showEmptyTable()

    def _update_table(self,
                      pit_time_loss_str: str,
                      relevant_rows: List[Dict[str, Any]],
                      ref_index: int,
                      page_item: QQuickItem):
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
            dnf_status = driver_info.get("dnf-status", "")
            if dnf_status in {"DNF", "DSQ"}:
                delta_str = dnf_status
                delta_color = "white"
            elif is_ref:
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

    def _is_active_car(self, row: Dict[str, Any]) -> bool:
        """Check if driver is active car."""
        status = row.get("driver-info", {}).get("dnf-status", "")
        return status not in ("DNF", "DSQ")
