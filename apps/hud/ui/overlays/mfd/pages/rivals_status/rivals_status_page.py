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
from typing import Any, Dict, List, final

from apps.hud.common import (format_tyre_wear, get_ers_cell_fields,
                             get_ref_row, get_relevant_race_table_rows,
                             get_wing_dmg_cell_fields, is_tt_session)
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.assets_loader import (load_team_logos_uri_dict,
                               load_tyre_icons_uri_dict)
from lib.config import (MfdPageId, OverlayId, PngSettings,
                        TimingTowerTyreInfoMode)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class RivalsStatusPage(MfdPageBase):
    """ERS, tyre and wing damage status of the cars around the reference driver."""
    OVERLAY_ID = OverlayId.RIVALS_STATUS
    KEY = MfdPageId.RIVALS_STATUS
    PAGE_QML_FILE: Path = Path(__file__).parent / "rivals_status_page.qml"

    def __init__(self, logger: logging.Logger, tyre_info_mode: TimingTowerTyreInfoMode):
        self._tyre_info_mode = tyre_info_mode
        super().__init__(logger)

    @classmethod
    def from_settings(cls, settings: PngSettings, logger: logging.Logger) -> "RivalsStatusPage":
        return cls(logger, settings.HUD.timing_tower_tyre_info_mode)

    @classmethod
    def standalone_show_title(cls, settings: PngSettings) -> bool:
        return settings.HUD.rivals_status_show_title

    @final
    def setup_page(self):
        self.num_adjacent_cars = 3
        self.team_logo_uris: defaultdict[str, str] = load_team_logos_uri_dict()
        self.tyre_icon_uris: defaultdict[str, str] = load_tyre_icons_uri_dict()

        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            if is_tt_session(data["event-type"]):
                self.set_qml_property("tableData", [])
                return
            table_entries = data["table-entries"]
            ref_row = get_ref_row(data)
            if not table_entries or not ref_row:
                self.set_qml_property("tableData", [])
                return

            ref_index = ref_row["driver-info"]["index"]
            relevant_rows = get_relevant_race_table_rows(table_entries, self.num_adjacent_cars, ref_index)
            self.set_qml_property("tableData", self._build_rows(relevant_rows, ref_index))

    def _build_rows(self, relevant_rows: List[Dict[str, Any]], ref_index: int) -> List[Dict[str, Any]]:
        rows_data = []
        for row_data in relevant_rows:
            driver_info: Dict[str, Any] = row_data.get("driver-info", {})
            tyre_info: Dict[str, Any] = row_data.get("tyre-info", {})
            telemetry_public = driver_info.get("telemetry-setting") == "Public"

            rows_data.append({
                "position": driver_info.get("position", 0),
                "teamIcon": self.team_logo_uris[driver_info.get("team", "UNKNOWN")],
                "name": driver_info.get("name", "UNKNOWN"),
                "isRef": driver_info.get("index", -1) == ref_index,
                # Subscript, not .get(): see TimingTowerOverlay - unmapped compounds need __missing__.
                "tyreIcon": self.tyre_icon_uris[tyre_info.get("visual-tyre-compound", "UNKNOWN")],
                "tyreWear": format_tyre_wear(tyre_info, telemetry_public, self._tyre_info_mode),
                **get_ers_cell_fields(row_data, telemetry_public),
                **get_wing_dmg_cell_fields(row_data.get("damage-info", {}), telemetry_public),
            })
        return rows_data
