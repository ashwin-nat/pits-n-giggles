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
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.assets_loader import (load_team_logos_uri_dict,
                               load_tyre_icons_uri_dict)
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TimingTowerOverlay(BaseOverlayQML):
    """QML-based timing tower overlay."""

    OVERLAY_ID: str = "timing_tower"
    QML_FILE: Path = Path(__file__).parent / "timing_tower.qml"

    MAX_SUPPORTED_CARS = 22

    def __init__(
        self,
        config: OverlaysConfig,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        num_adjacent_cars: int,
        windowed_overlay: bool
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
        """
        self.num_adjacent_cars = num_adjacent_cars
        self.total_rows = min(((self.num_adjacent_cars * 2) + 1), self.MAX_SUPPORTED_CARS)

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
        if self._root:
            self._root.setProperty("numRows", self.total_rows)

    def render_frame(self):
        """Not used - this overlay uses event-driven updates."""
        pass

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def _handle_race_update(data: Dict[str, Any]) -> None:
            """Handles race_table_update event.

            Args:
                data (Dict[str, Any]): The race table data from the server
            """
            if not self._root:
                return

            session_type = data["event-type"]

            if is_tt_session(session_type):
                self._show_error("TIME TRIAL NOT YET SUPPORTED")
                self._update_session_info("-- / --")
                return

            table_entries = data["table-entries"]
            if not table_entries:
                self.clear()
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                self._show_error("ERROR: Please check the logs")
                return

            ref_index = ref_row["driver-info"]["index"]

            table_entries.sort(key=lambda x: x["driver-info"]["position"])
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
        self._root.setProperty("sessionInfo", text)

    def _show_error(self, message: str):
        """Show an error message in the table area.

        Args:
            message (str): Error message to display
        """
        self._root.setProperty("showError", True)
        self._root.setProperty("errorMessage", message)
        self._root.setProperty("tableData", [])

    def _update_table_data(self, relevant_rows: List[Dict[str, Any]], ref_index: int):
        """Update the timing table data in QML.

        Args:
            relevant_rows (List[Dict[str, Any]]): List of row data
            ref_index (int): Index of reference driver
        """

        # Hide error message
        self._root.setProperty("showError", False)

        # Convert data to QML-friendly format
        qml_data = []
        for row_data in relevant_rows:
            driver_info = row_data.get("driver-info", {})
            delta_info = row_data.get("delta-info", {})
            tyre_info = row_data.get("tyre-info", {})
            ers_info = row_data.get("ers-info", {})
            warns_pens_info = row_data.get("warns-pens-info", {})

            telemetry_public = driver_info.get("telemetry-setting") == "Public"
            position = driver_info.get("position", 0)
            name = driver_info.get("name", "UNKNOWN")
            team = driver_info.get("team", "UNKNOWN")
            driver_idx = driver_info.get("index", -1)
            is_pitting = driver_info.get("is_pitting", False)
            drs = driver_info.get("drs", False)

            delta = delta_info.get("relative-delta", 0)
            delta_text = (
                "PIT" if is_pitting else
                "---" if driver_idx == ref_index or not delta else
                F1Utils.formatFloat(delta / 1000, precision=3, signed=True)
            )

            # Tyre info
            tyre_compound = tyre_info.get("visual-tyre-compound", "UNKNOWN")
            if telemetry_public:
                max_wear = F1Utils.getMaxTyreWear(tyre_info["current-wear"])
                tyre_wear_str = f"{F1Utils.formatFloat(max_wear['max-wear'], 0)}%"
            else:
                tyre_age = tyre_info.get("tyre-age", 0)
                tyre_wear_str = f"{tyre_age}L"

            # ERS info
            ers_mode = ers_info.get("ers-mode", "None")
            ers_perc = ers_info.get("ers-percent-float", 0.0)
            if telemetry_public:
                ers_text = f"{F1Utils.formatFloat(ers_perc, precision=0, signed=False)}%"
            else:
                ers_text = "N/A"

            # Penalties
            pens_sec = warns_pens_info.get("time-penalties", 0)
            num_dt = warns_pens_info.get("num-dt", 0)
            pens_str = (
                f"{num_dt}DT" if num_dt else
                f"+{pens_sec}sec" if pens_sec else
                ""
            )

            # Get icon URI
            team_icon_url = self.team_logo_uris[team]
            tyre_icon_url = self.tyre_icon_uris.get(tyre_compound, "")

            qml_data.append({
                "position": position,
                "teamIcon": team_icon_url,
                "name": name,
                "delta": delta_text,
                "tyreIcon": tyre_icon_url,
                "tyreWear": tyre_wear_str,
                "ers": ers_text,
                "ersMode": ers_mode,
                "drs": drs,
                "penalties": pens_str,
                "isReference": driver_idx == ref_index
            })

        self._root.setProperty("tableData", qml_data)

    def clear(self):
        """Clear all timing data."""
        if self._root:
            self._root.setProperty("sessionInfo", "-- / --")
            self._root.setProperty("tableData", [])
            self._root.setProperty("showError", False)

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
