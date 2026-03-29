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
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session,
                             is_tt_session)
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.assets_loader import (load_team_logos_uri_dict,
                               load_tyre_icons_uri_dict)
from lib.config import TIMING_TOWER_OVERLAY_ID, OverlayPosition
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TimingTowerOverlay(BaseOverlayQML):
    """QML-based timing tower overlay."""

    OVERLAY_ID: str = TIMING_TOWER_OVERLAY_ID
    QML_FILE: Path = Path(__file__).parent / "timing_tower.qml"

    MAX_SUPPORTED_CARS = 22

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        num_adjacent_cars: int,
        windowed_overlay: bool,
        show_team_logos: bool,
        show_tyre_info: bool,
        show_deltas: bool,
        show_ers_drs_info: bool,
        show_pens: bool,
        show_tl_warns: bool,
    ):
        """Initialize timing tower overlay.

        Args:
            config (OverlaysConfig): Overlay config
            logger (logging.Logger): Logger object
            locked (bool): Locked state
            opacity (int): Window opacity
            scale_factor (float): UI Scale factor (multiplier)
            num_adjacent_cars (int): Number of adjacent cars
            windowed_overlay (bool): Windowed overlay
            show_team_logos (bool): Show team logos
            show_tyre_info (bool): Show tyre info
            show_deltas (bool): Show deltas
            show_ers_drs_info (bool): Show ERS/DRS info
            show_pens (bool): Show penalties
            show_tl_warns (bool): Show Track Limit warnings
        """
        self.num_adjacent_cars = num_adjacent_cars
        self.total_rows = min(((self.num_adjacent_cars * 2) + 1), self.MAX_SUPPORTED_CARS)

        self.show_team_logos = show_team_logos
        self.show_tyre_info = show_tyre_info
        self.show_deltas = show_deltas
        self.show_ers_drs_info = show_ers_drs_info
        self.show_pens = show_pens
        self.show_tl_warns = show_tl_warns

        self.team_logo_uris: defaultdict[str, str] = defaultdict(str)
        self.tyre_icon_uris: Dict[str, str] = {}

        super().__init__(
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
            refresh_interval_ms=None  # Event-driven updates only
        )

        self._init_icons()
        self._init_event_handlers()

    def _init_icons(self):
        """Initialize tyre and team icons URI's"""
        self.team_logo_uris = load_team_logos_uri_dict()
        self.tyre_icon_uris = load_tyre_icons_uri_dict()

    def _setup_window(self):
        """Override to set numRows property after QML loads."""
        super()._setup_window()
        self.set_qml_property("numRows", self.total_rows)
        self.set_qml_property("showTeamLogos", self.show_team_logos)
        self.set_qml_property("showTyreInfo", self.show_tyre_info)
        self.set_qml_property("showDeltas", self.show_deltas)
        self.set_qml_property("showErsDrsInfo", self.show_ers_drs_info)
        self.set_qml_property("showPens", self.show_pens)
        self.set_qml_property("mode", "race")
        self.set_qml_property("ttTableData", [])

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def _handle_race_update(data: Dict[str, Any]) -> None:
            """Handles race_table_update event.

            Args:
                data (Dict[str, Any]): The race table data from the server
            """
            session_type = data["event-type"]

            if is_tt_session(session_type):
                self._process_time_trial(data)
                return

            self._process_non_time_trial(data, session_type)

    def _process_non_time_trial(self, data: Dict[str, Any], session_type: str) -> None:
        self.set_qml_property("mode", "race")

        table_entries = data["table-entries"]
        if not table_entries:
            self.clear()
            return

        ref_row = get_ref_row(data)
        if not ref_row:
            self._show_error("ERROR: Please check the logs")
            return

        ref_index = ref_row["driver-info"]["index"]
        relevant_rows = get_relevant_race_table_rows(table_entries, self.num_adjacent_cars, ref_index)

        if is_race_type_session(session_type):
            insert_relative_deltas_race(relevant_rows, ref_index)
        elif not is_tt_session(session_type):
            self._insert_relative_deltas_fp_quali(relevant_rows, ref_row)

        # Update QML with data
        self._update_table_data(relevant_rows, ref_index)

        # Update session info
        if session_type == 'None':
            self._update_session_info("----")
        elif self._should_show_lap_number(session_type):
            current_lap = data.get("current-lap", 0)
            total_laps = data.get("total-laps", 0)
            self._update_session_info(f"{session_type.upper()}    |    LAP {current_lap} / {total_laps}")
        else:
            time_remaining_sec = data.get("session-time-left", 0)
            minutes = int(time_remaining_sec // 60)
            seconds = int(time_remaining_sec % 60)
            self._update_session_info(f"{session_type.upper()}    |    TIME: {minutes:02d}:{seconds:02d}")

    def _update_session_info(self, text: str):
        """Update the session info label in QML.

        Args:
            text (str): Session info text
        """
        self.set_qml_property("sessionInfo", text)

    def _show_error(self, message: str):
        """Show an error message in the table area.

        Args:
            message (str): Error message to display
        """
        self.set_qml_property("showError", True)
        self.set_qml_property("errorMessage", message)
        self.set_qml_property("tableData", [])

    def _update_table_data(self, relevant_rows: List[Dict[str, Any]], ref_index: int):
        """Update the timing table data in QML.

        Args:
            relevant_rows (List[Dict[str, Any]]): List of row data
            ref_index (int): Index of reference driver
        """

        # Hide error message
        self.set_qml_property("showError", False)
        self.set_qml_property("tableData", [
            self._create_driver_row(row_data, ref_index)
            for row_data in relevant_rows
        ])

    def _create_driver_row(self, row_data: Dict[str, Any], ref_index: int) -> dict:
        """Create a single driver row for QML display.

        Args:
            row_data: Dictionary containing driver data
            ref_index: Index of reference driver

        Returns:
            Dictionary with formatted driver data for QML
        """
        driver_info: dict = row_data.get("driver-info", {})
        delta_info: dict = row_data.get("delta-info", {})
        tyre_info: dict = row_data.get("tyre-info", {})
        ers_info: dict = row_data.get("ers-info", {})
        warns_pens_info: dict = row_data.get("warns-pens-info", {})

        driver_idx = driver_info.get("index", -1)
        telemetry_public = driver_info.get("telemetry-setting") == "Public"

        return {
            "position": driver_info.get("position", 0),
            "teamIcon": self.team_logo_uris.get(driver_info.get("team", "UNKNOWN"), ""),
            "name": driver_info.get("name", "UNKNOWN"),
            "delta": self._format_delta(driver_info, delta_info, driver_idx, ref_index),
            "tyreIcon": self.tyre_icon_uris.get(tyre_info.get("visual-tyre-compound", "UNKNOWN"), ""),
            "tyreWear": self._format_tyre_wear(tyre_info, telemetry_public),
            "ers": self._format_ers(ers_info, telemetry_public),
            "ersMode": ers_info.get("ers-mode", "None"),
            "drs": driver_info.get("drs", False),
            "penalties": self._format_penalties(warns_pens_info),
            "isReference": driver_idx == ref_index
        }

    def _format_delta(
        self,
        driver_info: Dict[str, Any],
        delta_info: Dict[str, Any],
        driver_idx: int,
        ref_index: int
    ) -> str:
        """Format the delta time display.

        Args:
            driver_info: Driver information dictionary
            delta_info: Delta information dictionary
            driver_idx: Current driver index
            ref_index: Reference driver index

        Returns:
            Formatted delta string
        """
        if driver_info.get("is_pitting", False):
            return "PIT"

        dnf_status = driver_info.get("dnf-status", "")
        if dnf_status in {"DNF", "DSQ"}:
            return dnf_status

        delta = delta_info.get("relative-delta", 0)
        if driver_idx == ref_index or not delta:
            return "---"

        return F1Utils.formatFloat(delta / 1000, precision=3, signed=True)

    def _format_tyre_wear(self, tyre_info: Dict[str, Any], telemetry_public: bool) -> str:
        """Format tyre wear display.

        Args:
            tyre_info: Tyre information dictionary
            telemetry_public: Whether telemetry is public

        Returns:
            Formatted tyre wear string
        """
        wear = tyre_info.get("current-wear")
        if telemetry_public and wear:
            max_wear = F1Utils.getMaxTyreWear(wear)
            return f"{F1Utils.formatFloat(max_wear['max-wear'], 0)}%"

        tyre_age = tyre_info.get("tyre-age", 0)
        return f"{tyre_age}L"

    def _format_ers(self, ers_info: Dict[str, Any], telemetry_public: bool) -> str:
        """Format ERS display.

        Args:
            ers_info: ERS information dictionary
            telemetry_public: Whether telemetry is public

        Returns:
            Formatted ERS string
        """
        if not telemetry_public:
            return "N/A"

        ers_perc = ers_info.get("ers-percent-float", 0.0)
        return f"{F1Utils.formatFloat(ers_perc, precision=0, signed=False)}%"

    def _format_penalties(self, warns_pens_info: Dict[str, Any]) -> str:
        """Format penalties display.

        Args:
            warns_pens_info: Warnings and penalties information dictionary

        Returns:
            Formatted penalties string
        """
        num_dt = warns_pens_info.get("num-dt", 0)
        num_sg = warns_pens_info.get("num-sg", 0)
        pens_sec = warns_pens_info.get("time-penalties", 0) + (num_sg * 10)

        if num_dt > 0:
            return f"{num_dt}DT"

        if pens_sec > 0:
            return f"+{pens_sec}s"

        if self.show_tl_warns:
            tl_warns = warns_pens_info.get("corner-cutting-warnings", 0)
            return f"TL: {tl_warns}"

        return ""

    def clear(self):
        """Clear all timing data."""
        self.set_qml_property("sessionInfo", "-- / --")
        self.set_qml_property("tableData", [])
        self.set_qml_property("showError", False)
        self.set_qml_property("mode", "race")
        self.set_qml_property("ttTableData", [])

    def _should_show_lap_number(self, session_type: str) -> bool:
        """Check if it is a race/sprint session.

        Args:
            session_type (str): Session type

        Returns:
            bool: True if race/sprint session
        """
        return is_race_type_session(session_type)

    def _insert_relative_deltas_fp_quali(
        self,
        relevant_rows: List[Dict[str, Any]],
        ref_row: Dict[str, Any]
    ) -> None:
        """Insert relative deltas for FP/Quali mode.

        Args:
            relevant_rows (List[Dict[str, Any]]): List of relevant rows
            ref_row (Dict[str, Any]): The reference row
        """
        if not ref_row:
            self.logger.warning('<<TIMING_TOWER>> Reference row is None!')
            return

        ref_best_lap_ms = ref_row["lap-info"]["best-lap"]["lap-time-ms"]

        for row in relevant_rows:
            best_lap_ms = row["lap-info"]["best-lap"]["lap-time-ms"]
            if ref_best_lap_ms is None or best_lap_ms is None:
                row["delta-info"]["relative-delta"] = 0
            else:
                row["delta-info"]["relative-delta"] = best_lap_ms - ref_best_lap_ms

    def _process_time_trial(self, data: Dict[str, Any]) -> None:
        """Process incoming time trial telemetry data and update the QML overlay.

        Extracts the current lap, personal best, session best, and rival lap
        from the payload and pushes them to the TT table in QML. Clears the
        overlay if the required data is absent.

        Args:
            data (Dict[str, Any]): Full telemetry payload containing a "tt-data" key.
        """
        tt_data_outer: dict = data.get("tt-data", {})
        tt_data_inner = tt_data_outer.get("tt-data")
        if not tt_data_outer or not tt_data_inner:
            self.clear()
            return

        curr_lap_num = tt_data_outer.get("current-lap", 0)

        pb_dataset = tt_data_inner.get("personal-best-data-set", {})
        pb_ms = self._extract_tt_ms(pb_dataset)  # None values when PB not set

        table_data = [
            self._get_tt_curr_lap(tt_data_outer, pb_ms),
            self._get_tt_pb_lap(tt_data_inner),
            self._get_tt_sb_lap(tt_data_inner, pb_ms),
            self._get_tt_rival_lap(tt_data_inner, pb_ms),
        ]

        self.set_qml_property("mode", "tt")
        self.set_qml_property("ttTableData", table_data)
        self._update_session_info(f"TIME TRIAL    |    LAP {curr_lap_num}")

    @staticmethod
    def _extract_tt_ms(dataset: dict) -> Dict[str, Any]:
        """Extract raw millisecond values from a TimeTrialDataSet JSON dict.

        Args:
            dataset (dict): TimeTrialDataSet.toJSON() output

        Returns:
            dict with keys lap/s1/s2/s3, values are int ms or None if invalid
        """
        if not dataset or not dataset.get("is-valid"):
            return {"lap": None, "s1": None, "s2": None, "s3": None}
        return {
            "lap": dataset.get("lap-time-ms") or None,
            "s1": dataset.get("sector-1-time-ms") or None,
            "s2": dataset.get("sector-2-time-in-ms") or None,
            "s3": dataset.get("sector3-time-in-ms") or None,
        }

    @staticmethod
    def _format_tt_delta(row_ms, pb_ms) -> str:
        """Compute and format a signed delta against the PB value.

        Args:
            row_ms: Row's millisecond value (int or None)
            pb_ms: PB millisecond value (int or None)

        Returns:
            Signed seconds string like "+1.234" / "-0.456", or "---"
        """
        if not row_ms or not pb_ms:
            return "---"
        return F1Utils.formatFloat((row_ms - pb_ms) / 1000, precision=3, signed=True)

    def _tt_row_from_dataset(self, label: str, dataset: dict, pb_ms: Dict[str, Any] = None) -> dict:
        """Build a TT table row dict from a TimeTrialDataSet JSON dict.

        Args:
            label (str): Row label (e.g. "SB", "Rival")
            dataset (dict): TimeTrialDataSet.toJSON() output
            pb_ms (dict): PB ms values from _extract_tt_ms; if provided, time strings are deltas vs PB

        Returns:
            dict: Row data for QML
        """
        if not dataset or not dataset.get("is-valid"):
            return {
                "label": label,
                "lap-time-str": "---",
                "s1-time-str": "---",
                "s2-time-str": "---",
                "s3-time-str": "---",
            }
        if pb_ms and pb_ms["lap"]:
            return {
                "label": label,
                "lap-time-str": self._format_tt_delta(dataset.get("lap-time-ms"), pb_ms["lap"]),
                "s1-time-str": self._format_tt_delta(dataset.get("sector-1-time-ms"), pb_ms["s1"]),
                "s2-time-str": self._format_tt_delta(dataset.get("sector-2-time-in-ms"), pb_ms["s2"]),
                "s3-time-str": self._format_tt_delta(dataset.get("sector3-time-in-ms"), pb_ms["s3"]),
            }
        return {
            "label": label,
            "lap-time-str": dataset.get("lap-time-str", "---"),
            "s1-time-str": dataset.get("sector-1-time-str", "---"),
            "s2-time-str": dataset.get("sector-2-time-str", "---"),
            "s3-time-str": dataset.get("sector-3-time-str", "---"),
        }

    def _get_tt_curr_lap(self, tt_data_outer: dict, pb_ms: Dict[str, Any] = None) -> dict:
        """Get the most recently completed lap from session history.

        Args:
            tt_data_outer (dict): Outer TT data dict containing session-history
            pb_ms (dict): PB ms values from _extract_tt_ms; if provided, time strings are deltas vs PB

        Returns:
            dict: Row data for QML
        """
        session_history = tt_data_outer.get("session-history")
        if session_history:
            lap_history = session_history.get("lap-history-data", [])
            if lap_history:
                last_lap = lap_history[-1]
                if pb_ms and pb_ms["lap"]:
                    return {
                        "label": "Current",
                        "lap-time-str": self._format_tt_delta(last_lap.get("lap-time-in-ms"), pb_ms["lap"]),
                        "s1-time-str": self._format_tt_delta(last_lap.get("sector-1-time-in-ms"), pb_ms["s1"]),
                        "s2-time-str": self._format_tt_delta(last_lap.get("sector-2-time-in-ms"), pb_ms["s2"]),
                        "s3-time-str": self._format_tt_delta(last_lap.get("sector-3-time-in-ms"), pb_ms["s3"]),
                    }
                return {
                    "label": "Current",
                    "lap-time-str": last_lap.get("lap-time-str", "---"),
                    "s1-time-str": last_lap.get("sector-1-time-str", "---"),
                    "s2-time-str": last_lap.get("sector-2-time-str", "---"),
                    "s3-time-str": last_lap.get("sector-3-time-str", "---"),
                }
        return {
            "label": "Current",
            "lap-time-str": "---",
            "s1-time-str": "---",
            "s2-time-str": "---",
            "s3-time-str": "---",
        }

    def _get_tt_pb_lap(self, tt_data: dict) -> dict:
        """Get the player's all-time personal best lap row.

        Args:
            tt_data (dict): Inner TT data dict (PacketTimeTrialData.tt-data).

        Returns:
            dict: Row data for QML.
        """
        return self._tt_row_from_dataset("PB", tt_data.get("personal-best-data-set", {}))

    def _get_tt_sb_lap(self, tt_data: dict, pb_ms: Dict[str, Any] = None) -> dict:
        """Get the player's best lap for the current session row.

        Args:
            tt_data (dict): Inner TT data dict (PacketTimeTrialData.tt-data).
            pb_ms (dict): PB ms values from _extract_tt_ms; if provided, time strings are deltas vs PB

        Returns:
            dict: Row data for QML.
        """
        return self._tt_row_from_dataset("SB", tt_data.get("player-session-best-data-set", {}), pb_ms)

    def _get_tt_rival_lap(self, tt_data: dict, pb_ms: Dict[str, Any] = None) -> dict:
        """Get the rival's session best lap row.

        Args:
            tt_data (dict): Inner TT data dict (PacketTimeTrialData.tt-data).
            pb_ms (dict): PB ms values from _extract_tt_ms; if provided, time strings are deltas vs PB

        Returns:
            dict: Row data for QML.
        """
        return self._tt_row_from_dataset("Rival", tt_data.get("rival-session-best-data-set", {}), pb_ms)
