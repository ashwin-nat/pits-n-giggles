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

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, final

from apps.hud.common import get_ers_mode_color, get_ref_row_index
from apps.hud.ui.overlays.mfd.pages.standalone_base import \
    StandalonePageOverlay
from lib.config import MfdPageId, OverlayId
from lib.track_segment_info import TrackSegmentsDatabase

from .utils import get_traffic_window, resolve_location, sort_by_rel_distance

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_DRIVER_STATUS_IN_GARAGE = "IN_GARAGE"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TrafficMonitorPage(StandalonePageOverlay):
    """Traffic Monitor MFD Page — nearest 5 cars behind sorted by lap distance."""
    OVERLAY_ID = OverlayId.TRAFFIC_MONITOR
    KEY = MfdPageId.TRAFFIC_MONITOR
    PAGE_QML_FILE: Path = Path(__file__).parent / "traffic_monitor_page.qml"

    NUM_BEHIND = 5

    @final
    def on_page_activated(self):
        pass

    @final
    def setup_overlay(self):
        self.tracks_db = TrackSegmentsDatabase(Path(__file__).parents[7] / "assets/track-segments")

        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            table_entries: Optional[List] = data.get("table-entries")
            circuit_len: Optional[float] = data.get("circuit-len")
            circuit_num: Optional[int] = data.get("circuit-enum-value")

            if not table_entries or not circuit_len:
                self._show_empty()
                return

            ref_arr_index = get_ref_row_index(data)
            if ref_arr_index is None:
                self._show_empty()
                return

            ref_row = table_entries[ref_arr_index]
            ref_index: Optional[int] = ref_row["driver-info"]["index"]
            assert ref_index is not None

            ref_status = ref_row.get("lap-info", {}).get("curr-lap", {}).get("driver-status")
            if ref_status == _DRIVER_STATUS_IN_GARAGE:
                self._show_in_garage()
                return

            ref_lap_dist: Optional[float] = ref_row.get("lap-info", {}).get("lap-distance")
            if ref_lap_dist is None:
                self._show_empty()
                return

            active_entries = [
                e for e in table_entries
                if e.get("lap-info", {}).get("curr-lap", {}).get("driver-status") != _DRIVER_STATUS_IN_GARAGE
            ]

            sorted_entries = sort_by_rel_distance(active_entries, ref_lap_dist, circuit_len)
            if not sorted_entries:
                self._show_empty()
                return

            ref_pos = next(
                (i for i, (_, row) in enumerate(sorted_entries) if row["driver-info"]["index"] == ref_index),
                None,
            )
            if ref_pos is None:
                self._show_empty()
                return

            window = get_traffic_window(sorted_entries, ref_pos, self.NUM_BEHIND)
            self.set_qml_property("tableData", self._build_rows(window, ref_index, circuit_num))
            self.set_qml_property("viewState", "table")

    def _show_empty(self) -> None:
        self.set_qml_property("tableData", [])
        self.set_qml_property("viewState", "empty")

    def _show_in_garage(self) -> None:
        self.set_qml_property("tableData", [])
        self.set_qml_property("viewState", "inGarage")

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
            "ersColor":     get_ers_mode_color(ers_mode, row.get('2026-regs-info', {}).get('2026-regs-enabled', False), row.get('2026-regs-info', {}).get('overtake-active', False)),
            "ersPercent":   f"{ers_info.get('ers-percent-float', 0.0) or 0.0:.0f}%",
            "drs":          driver_info.get("drs-activated", False) or False,
            "relDist":      f"+{rel_dist_m:.0f}m",
            "relDistColor": "#44FF44",
            "isRef":        is_ref,
            "location":     resolve_location(
                                self.tracks_db, circuit_num,
                                lap_info.get("lap-distance"),
                                curr_lap_info.get("sector"),
                            ),
        }
