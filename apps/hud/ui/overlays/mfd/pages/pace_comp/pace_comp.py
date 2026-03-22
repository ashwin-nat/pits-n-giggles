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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtQuick import QQuickItem

from apps.hud.common import get_ref_row, get_relevant_race_table_rows
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.f1_types import F1Utils

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------


class PaceCompPage(MfdPageBase):
    """Pace Comparison MFD Page."""
    KEY = "pace_comp"
    QML_FILE: Path = Path(__file__).parent / "pace_comp_page.qml"

    NUM_ADJ_CARS = 2

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        super().__init__(overlay, logger)
        self._init_event_handlers()

    # -- Event wiring ----------------------------------------------------------

    def _init_event_handlers(self):
        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            page_item = self._page_item
            table_entries = data.get("table-entries")
            if not table_entries:
                self._show_empty_table(page_item)
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                self._show_empty_table(page_item)
                return

            ref_idx = ref_row["driver-info"]["index"]
            relevant_rows = get_relevant_race_table_rows(table_entries, self.NUM_ADJ_CARS, ref_idx)
            self._update_table(relevant_rows, ref_row, page_item)

    # -- Table update ----------------------------------------------------------

    def _update_table(self,
                      relevant_rows: List[Dict[str, Any]],
                      ref_row: Dict[str, Any],
                      page_item: QQuickItem) -> None:
        ref_idx   = ref_row["driver-info"]["index"]
        ref_times = ref_row.get("lap-info", {}).get("last-lap", {})
        ref_s1_ms  = ref_times.get("s1-time-ms")
        ref_s2_ms  = ref_times.get("s2-time-ms")
        ref_s3_ms  = ref_times.get("s3-time-ms")
        ref_lap_ms = ref_times.get("lap-time-ms")

        rows_data = [
            self._build_row(row, ref_idx, ref_s1_ms, ref_s2_ms, ref_s3_ms, ref_lap_ms)
            for row in relevant_rows
        ]
        self._set_rows(page_item, rows_data)

    def _build_row(self,
                   row_data: Dict[str, Any],
                   ref_idx: int,
                   ref_s1_ms:  Optional[int],
                   ref_s2_ms:  Optional[int],
                   ref_s3_ms:  Optional[int],
                   ref_lap_ms: Optional[int]) -> Dict[str, Any]:
        driver_info: Dict[str, Any] = row_data.get("driver-info", {})
        last_lap:    Dict[str, Any] = row_data.get("lap-info", {}).get("last-lap", {})

        is_ref = driver_info.get("index", -1) == ref_idx

        if is_ref:
            s1_str, s2_str, s3_str, lap_str = self._format_ref_times(
                ref_s1_ms, ref_s2_ms, ref_s3_ms, ref_lap_ms)
        else:
            s1_str, s2_str, s3_str, lap_str = self._format_delta_times(
                last_lap, ref_s1_ms, ref_s2_ms, ref_s3_ms, ref_lap_ms)

        return {
            "position": str(driver_info.get("position", 0)),
            "team":     driver_info.get("team", ""),
            "name":     driver_info.get("name", ""),
            "s1":       s1_str,
            "s2":       s2_str,
            "s3":       s3_str,
            "lap":      lap_str,
            "isRef":    is_ref,
        }

    # -- Formatting helpers ----------------------------------------------------

    @staticmethod
    def _format_ref_times(s1_ms: Optional[int],
                          s2_ms: Optional[int],
                          s3_ms: Optional[int],
                          lap_ms: Optional[int]):
        """Absolute sector/lap times for the reference driver."""
        s1  = F1Utils.millisecondsToSecondsMilliseconds(s1_ms)  if s1_ms  is not None else "--:--"
        s2  = F1Utils.millisecondsToSecondsMilliseconds(s2_ms)  if s2_ms  is not None else "--:--"
        s3  = F1Utils.millisecondsToSecondsMilliseconds(s3_ms)  if s3_ms  is not None else "--:--"
        lap = F1Utils.millisecondsToMinutesSecondsMilliseconds(lap_ms) if lap_ms is not None else "--:--"
        return s1, s2, s3, lap

    @staticmethod
    def _format_delta_times(last_lap: Dict[str, Any],
                            ref_s1_ms:  Optional[int],
                            ref_s2_ms:  Optional[int],
                            ref_s3_ms:  Optional[int],
                            ref_lap_ms: Optional[int]):
        """Signed deltas vs the reference driver (ref − other)."""
        def _delta(other_ms: Optional[int], ref_ms: Optional[int]) -> str:
            if other_ms is None or ref_ms is None:
                return "--:--"
            return F1Utils.formatFloat((ref_ms - other_ms) / 1000.0, precision=3, signed=True)

        return (
            _delta(last_lap.get("s1-time-ms"),  ref_s1_ms),
            _delta(last_lap.get("s2-time-ms"),  ref_s2_ms),
            _delta(last_lap.get("s3-time-ms"),  ref_s3_ms),
            _delta(last_lap.get("lap-time-ms"), ref_lap_ms),
        )

    # -- QML helpers -----------------------------------------------------------

    def _show_empty_table(self, page_item: QQuickItem) -> None:
        """Clear the table."""
        self._set_rows(page_item, [])

    def _set_rows(self, page_item: QQuickItem, rows: List[Dict[str, Any]]) -> None:
        """Push row data to QML."""
        page_item.setProperty("rows", rows)
