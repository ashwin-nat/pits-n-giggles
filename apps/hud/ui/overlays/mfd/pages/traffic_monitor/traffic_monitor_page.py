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
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, final

from PySide6.QtQuick import QQuickItem

from apps.hud.common import get_adjacent_positions, get_ref_row_index
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.track_segment_info import TrackSegmentsDatabase
from lib.config import MfdPageId

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_ERS_MODE_COLORS: Dict[str, str] = {
    "Medium":   "#e6d800",
    "Hotlap":   "#00e676",
    "Overtake": "#ff1744",
}
_ERS_MODE_COLOR_DEFAULT = "#444444"

_DRIVER_STATUS_IN_GARAGE = "IN_GARAGE"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TrafficMonitorPage(MfdPageBase):
    """Traffic Monitor MFD Page — nearest 2 cars ahead/behind sorted by lap distance."""
    KEY = MfdPageId.TRAFFIC_MONITOR
    QML_FILE: Path = Path(__file__).parent / "traffic_monitor_page.qml"

    NUM_ADJACENT = 2

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):

        self.tracks_db = TrackSegmentsDatabase(Path(__file__).parents[7] / "assets/track-segments")

        super().__init__(overlay, logger)
        self._init_event_handlers()

    @final
    def on_page_activated(self, _: QQuickItem):
        pass

    def _init_event_handlers(self):
        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            page_item = self._page_item
            table_entries = data.get("table-entries")
            circuit_len = data.get("circuit-len")
            circuit_num = data.get("circuit-enum-value")

            if not table_entries or not circuit_len:
                page_item.showEmptyTable()
                return

            ref_arr_index = get_ref_row_index(data)
            if ref_arr_index is None:
                page_item.showEmptyTable()
                return

            ref_row = table_entries[ref_arr_index]
            ref_index = ref_row["driver-info"]["index"]
            assert ref_index is not None

            # Show IN GARAGE state when the ref driver is in the garage
            ref_status = ref_row.get("lap-info", {}).get("curr-lap", {}).get("driver-status")
            if ref_status == _DRIVER_STATUS_IN_GARAGE:
                page_item.showInGarage()
                return

            # Filter out IN_GARAGE cars from the field
            active_entries = [
                e for e in table_entries
                if e.get("lap-info", {}).get("curr-lap", {}).get("driver-status") != _DRIVER_STATUS_IN_GARAGE
            ]

            sorted_entries = self._sort_by_track_distance(active_entries, circuit_len)
            if not sorted_entries:
                page_item.showEmptyTable()
                return

            ref_pos_in_sorted = next(
                (i for i, (_, row) in enumerate(sorted_entries)
                 if row["driver-info"]["index"] == ref_index),
                None,
            )
            if ref_pos_in_sorted is None:
                page_item.showEmptyTable()
                return

            window = self._get_window(sorted_entries, ref_pos_in_sorted)
            ref_total_dist = sorted_entries[ref_pos_in_sorted][0]
            rows_data = self._build_rows(window, ref_index, ref_total_dist, circuit_num)
            page_item.updateData(rows_data)

    # ------------------------------------------------------------------------------------------------------------------

    def _sort_by_track_distance(
        self,
        table_entries: List[Dict[str, Any]],
        circuit_len: float,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Return (normalised_lap_dist, row) pairs sorted descending — furthest ahead first."""
        result = []
        for row in table_entries:
            lap_dist = row.get("lap-info", {}).get("lap-distance")
            if lap_dist is None:
                continue
            result.append((lap_dist % circuit_len, row))
        result.sort(key=lambda x: x[0], reverse=True)
        return result

    def _get_window(
        self,
        sorted_entries: List[Tuple[float, Dict[str, Any]]],
        ref_pos: int,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Return up to NUM_ADJACENT ahead + ref + NUM_ADJACENT behind, clamped to available cars."""
        total = len(sorted_entries)
        lower_bound, upper_bound = get_adjacent_positions(ref_pos + 1, total, self.NUM_ADJACENT)
        if lower_bound is None:
            return [sorted_entries[ref_pos]]
        return sorted_entries[lower_bound - 1 : upper_bound]

    def _build_rows(
        self,
        window: List[Tuple[float, Dict[str, Any]]],
        ref_index: int,
        ref_total_dist: float,
        circuit_num: int,
    ) -> List[Dict[str, Any]]:
        rows_data = []
        for total_dist, row in window:
            driver_info: Dict[str, Any] = row.get("driver-info", {})
            ers_info: Dict[str, Any] = row.get("ers-info", {})
            lap_info: Dict[str, Any] = row.get("lap-info", {})
            curr_lap_info: Dict[str, Any] = lap_info.get("curr-lap", {})

            is_ref = (driver_info.get("index", -1) == ref_index)

            rel_dist_m = ref_total_dist - total_dist  # negative = other is ahead
            if is_ref:
                rel_dist_str = "---"
                rel_dist_color = "white"
            else:
                rel_dist_str = f"{rel_dist_m:+.0f}m"
                rel_dist_color = "#FF4444" if rel_dist_m < 0 else "#44FF44"

            ers_mode: str = ers_info.get("ers-mode") or "None"
            ers_perc_float: float = ers_info.get("ers-percent-float", 0.0) or 0.0
            drs_active: bool = driver_info.get("drs-activated", False) or False

            lap_dist = lap_info.get("lap-distance")
            assert lap_dist is not None
            segment_info = self.tracks_db.get_segment_info(circuit_num, lap_dist)
            location_str = curr_lap_info.get("sector", "---")

            if segment_info:
                match segment_info.TYPE:
                    case "corner":
                        location_str = f"T{segment_info.corner_number}"
                    case "complex_corner":
                        location_str = segment_info.render()["turns"]

            rows_data.append({
                "team": driver_info.get("team", ""),
                "name": driver_info.get("name", ""),
                "ersColor": _ERS_MODE_COLORS.get(ers_mode, _ERS_MODE_COLOR_DEFAULT),
                "ersPercent": f"{ers_perc_float:.0f}%",
                "drs": drs_active,
                "relDist": rel_dist_str,
                "relDistColor": rel_dist_color,
                "isRef": is_ref,
                "location": location_str,
            })
        return rows_data
