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

from pathlib import Path
from typing import Any, Dict, List, Optional, final

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             is_race_type_session, is_tt_session)
from apps.hud.ui.overlays.mfd.pages.standalone_base import \
    StandalonePageOverlay
from lib.config import MfdPageId, OverlayId
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------


class PaceCompPage(StandalonePageOverlay):
    """Pace Comparison MFD Page."""
    OVERLAY_ID = OverlayId.PACE_COMP
    KEY = MfdPageId.PACE_COMP
    PAGE_QML_FILE: Path = Path(__file__).parent / "pace_comp_page.qml"

    NUM_ADJ_CARS = 2

    # -- Event wiring ----------------------------------------------------------

    @final
    def setup_overlay(self):
        @self.on_page_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            session_type = data.get("event-type", "")

            if is_tt_session(session_type):
                self._update_table_tt(data)
                return

            table_entries = data.get("table-entries")
            if not table_entries:
                self._show_empty_table()
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                self._show_empty_table()
                return

            use_best_lap = not is_race_type_session(session_type)
            ref_idx = ref_row["driver-info"]["index"]
            relevant_rows = get_relevant_race_table_rows(table_entries, self.NUM_ADJ_CARS, ref_idx)
            self._update_table(relevant_rows, ref_row, use_best_lap)

    # -- Table update ----------------------------------------------------------

    def _update_table(self,
                      relevant_rows: List[Dict[str, Any]],
                      ref_row: Dict[str, Any],
                      use_best_lap: bool) -> None:
        ref_idx   = ref_row["driver-info"]["index"]
        lap_key   = "best-lap" if use_best_lap else "last-lap"
        ref_times = ref_row.get("lap-info", {}).get(lap_key, {})
        ref_s1_ms  = ref_times.get("s1-time-ms")
        ref_s2_ms  = ref_times.get("s2-time-ms")
        ref_s3_ms  = ref_times.get("s3-time-ms")
        ref_lap_ms = ref_times.get("lap-time-ms")

        rows_data = [
            self._build_row(row, ref_idx, ref_s1_ms, ref_s2_ms, ref_s3_ms, ref_lap_ms, lap_key)
            for row in relevant_rows
        ]
        self._set_rows(rows_data)

    def _build_row(self,
                   row_data: Dict[str, Any],
                   ref_idx: int,
                   ref_s1_ms:  Optional[int],
                   ref_s2_ms:  Optional[int],
                   ref_s3_ms:  Optional[int],
                   ref_lap_ms: Optional[int],
                   lap_key: str) -> Dict[str, Any]:
        driver_info: Dict[str, Any] = row_data.get("driver-info", {})
        lap_times:   Dict[str, Any] = row_data.get("lap-info", {}).get(lap_key, {})

        is_ref = driver_info.get("index", -1) == ref_idx

        if is_ref:
            s1_str, s2_str, s3_str, lap_str = self._format_ref_times(
                ref_s1_ms, ref_s2_ms, ref_s3_ms, ref_lap_ms)
        else:
            s1_str, s2_str, s3_str, lap_str = self._format_delta_times(
                lap_times, ref_s1_ms, ref_s2_ms, ref_s3_ms, ref_lap_ms)

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

    # -- Time trial ------------------------------------------------------------

    def _update_table_tt(self, data: Dict[str, Any]) -> None:
        tt_data_outer: Dict[str, Any] = data.get("tt-data", {})
        tt_data_inner: Dict[str, Any] = tt_data_outer.get("tt-data", {}) if tt_data_outer else {}
        if not tt_data_outer or not tt_data_inner:
            self._show_empty_table()
            return

        pb_dataset  = tt_data_inner.get("personal-best-data-set", {})
        sb_dataset  = tt_data_inner.get("player-session-best-data-set", {})
        rv_dataset  = tt_data_inner.get("rival-session-best-data-set", {})
        last_lap    = tt_data_outer.get("last-lap-info", {})

        pb_ms = self._extract_tt_ms(pb_dataset)

        rows = [
            self._build_tt_row("PB",    pb_dataset,  ref_ms=None),
            self._build_tt_row("SB",    sb_dataset,  ref_ms=pb_ms),
            self._build_tt_row("Rival", rv_dataset,  ref_ms=pb_ms),
            self._build_tt_row("Last",  last_lap,    ref_ms=pb_ms, last_lap=True),
        ]
        self._set_rows(rows)

    @staticmethod
    def _extract_tt_ms(dataset: Dict[str, Any]) -> Dict[str, Optional[int]]:
        if not dataset or not dataset.get("is-valid"):
            return {"lap": None, "s1": None, "s2": None, "s3": None}
        return {
            "lap": dataset.get("lap-time-ms") or None,
            "s1":  dataset.get("sector-1-time-ms") or None,
            "s2":  dataset.get("sector-2-time-in-ms") or None,
            "s3":  dataset.get("sector3-time-in-ms") or None,
        }

    @staticmethod
    def _tt_delta(row_ms: Optional[int], ref_ms: Optional[int]) -> str:
        if row_ms is None or ref_ms is None:
            return "---"
        return F1Utils.formatFloat((row_ms - ref_ms) / 1000.0, precision=3, signed=True)

    def _build_tt_row(self,
                      label: str,
                      dataset: Dict[str, Any],
                      ref_ms: Optional[Dict[str, Optional[int]]],
                      last_lap: bool = False) -> Dict[str, Any]:
        """Build a pace-comp row from a TT dataset or last-lap dict.

        For PB (ref_ms=None) absolute times are shown.
        For SB/Rival/Last, signed deltas vs PB are shown.
        last_lap=True uses the flat last-lap-info key layout instead of the
        TimeTrialDataSet layout.
        """
        if last_lap:
            valid = bool(dataset)
            lap_ms = dataset.get("lap-time-ms") if valid else None
            s1_ms  = dataset.get("s1-time-ms")  if valid else None
            s2_ms  = dataset.get("s2-time-ms")  if valid else None
            s3_ms  = dataset.get("s3-time-ms")  if valid else None
        else:
            valid = bool(dataset and dataset.get("is-valid"))
            lap_ms = dataset.get("lap-time-ms")          if valid else None
            s1_ms  = dataset.get("sector-1-time-ms")     if valid else None
            s2_ms  = dataset.get("sector-2-time-in-ms")  if valid else None
            s3_ms  = dataset.get("sector3-time-in-ms")   if valid else None

        if ref_ms is None:
            # PB row — absolute times
            s1_str  = F1Utils.millisecondsToSecondsMilliseconds(s1_ms)          if s1_ms  is not None else "---"
            s2_str  = F1Utils.millisecondsToSecondsMilliseconds(s2_ms)          if s2_ms  is not None else "---"
            s3_str  = F1Utils.millisecondsToSecondsMilliseconds(s3_ms)          if s3_ms  is not None else "---"
            lap_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(lap_ms)  if lap_ms is not None else "---"
        else:
            s1_str  = self._tt_delta(s1_ms,  ref_ms["s1"])
            s2_str  = self._tt_delta(s2_ms,  ref_ms["s2"])
            s3_str  = self._tt_delta(s3_ms,  ref_ms["s3"])
            lap_str = self._tt_delta(lap_ms, ref_ms["lap"])

        return {
            "position": "",
            "team":     "",
            "name":     label,
            "s1":       s1_str,
            "s2":       s2_str,
            "s3":       s3_str,
            "lap":      lap_str,
            "isRef":    ref_ms is None,
        }

    # -- QML helpers -----------------------------------------------------------

    def _show_empty_table(self) -> None:
        """Clear the table."""
        self._set_rows([])

    def _set_rows(self, rows: List[Dict[str, Any]]) -> None:
        """Push row data to QML."""
        self.set_page_property("rows", rows)
