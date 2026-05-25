# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, final

from PySide6.QtQuick import QQuickItem

from apps.hud.common import get_ref_row_index
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import MfdPageId
from lib.track_segment_info import TrackSegmentsDatabase

from .utils import get_traffic_window, resolve_location, sort_by_rel_distance

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
            table_entries: Optional[List] = data.get("table-entries")
            circuit_len: Optional[float] = data.get("circuit-len")
            circuit_num: Optional[int] = data.get("circuit-enum-value")

            if not table_entries or not circuit_len:
                page_item.showEmptyTable()
                return

            ref_arr_index = get_ref_row_index(data)
            if ref_arr_index is None:
                page_item.showEmptyTable()
                return

            ref_row = table_entries[ref_arr_index]
            ref_index: Optional[int] = ref_row["driver-info"]["index"]
            assert ref_index is not None

            ref_status = ref_row.get("lap-info", {}).get("curr-lap", {}).get("driver-status")
            if ref_status == _DRIVER_STATUS_IN_GARAGE:
                page_item.showInGarage()
                return

            ref_lap_dist: Optional[float] = ref_row.get("lap-info", {}).get("lap-distance")
            if ref_lap_dist is None:
                page_item.showEmptyTable()
                return

            active_entries = [
                e for e in table_entries
                if e.get("lap-info", {}).get("curr-lap", {}).get("driver-status") != _DRIVER_STATUS_IN_GARAGE
            ]

            sorted_entries = sort_by_rel_distance(active_entries, ref_lap_dist, circuit_len)
            if not sorted_entries:
                page_item.showEmptyTable()
                return

            ref_pos = next(
                (i for i, (_, row) in enumerate(sorted_entries) if row["driver-info"]["index"] == ref_index),
                None,
            )
            if ref_pos is None:
                page_item.showEmptyTable()
                return

            window = get_traffic_window(sorted_entries, ref_pos, self.NUM_ADJACENT)
            page_item.updateData(self._build_rows(window, ref_index, circuit_num))

    # ------------------------------------------------------------------------------------------------------------------

    def _build_rows(
        self,
        window: List[Tuple[float, Dict[str, Any]]],
        ref_index: int,
        circuit_num: Optional[int],
    ) -> List[Dict[str, Any]]:
        return [self._build_row(rel_dist_m, row, ref_index, circuit_num) for rel_dist_m, row in window]

    def _build_row(
        self,
        rel_dist_m: float,
        row: Dict[str, Any],
        ref_index: int,
        circuit_num: Optional[int],
    ) -> Dict[str, Any]:
        driver_info: Dict[str, Any] = row.get("driver-info", {})
        ers_info: Dict[str, Any] = row.get("ers-info", {})
        lap_info: Dict[str, Any] = row.get("lap-info", {})
        curr_lap_info: Dict[str, Any] = lap_info.get("curr-lap", {})

        is_ref = (driver_info.get("index", -1) == ref_index)
        ers_mode: str = ers_info.get("ers-mode") or "None"

        return {
            "team":         driver_info.get("team", ""),
            "name":         driver_info.get("name", ""),
            "ersColor":     _ERS_MODE_COLORS.get(ers_mode, _ERS_MODE_COLOR_DEFAULT),
            "ersPercent":   f"{ers_info.get('ers-percent-float', 0.0) or 0.0:.0f}%",
            "drs":          driver_info.get("drs-activated", False) or False,
            "relDist":      "---" if is_ref else f"{rel_dist_m:+.0f}m",
            "relDistColor": "white" if is_ref else ("#FF4444" if rel_dist_m < 0 else "#44FF44"),
            "isRef":        is_ref,
            "location":     resolve_location(
                                self.tracks_db, circuit_num,
                                lap_info.get("lap-distance"),
                                curr_lap_info.get("sector"),
                            ),
        }
