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

from apps.hud.common import get_ref_row
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.assets_loader import load_tyre_icons_uri_dict
from lib.config import MfdPageId, OverlayId, PngSettings

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyresStatusPage(MfdPageBase):
    """Per-tyre compound, wear, core temperature and surface temperature of the reference driver."""
    OVERLAY_ID = OverlayId.TYRES_STATUS
    KEY = MfdPageId.TYRES_STATUS
    PAGE_QML_FILE: Path = Path(__file__).parent / "tyres_status_page.qml"

    # (wear key, temp key, QML position key); order is the on-screen order FL, FR, RL, RR
    TYRES = (
        ("front-left", "fl", "FL"),
        ("front-right", "fr", "FR"),
        ("rear-left", "rl", "RL"),
        ("rear-right", "rr", "RR"),
    )

    @classmethod
    def from_settings(cls, settings: PngSettings, logger: logging.Logger) -> "TyresStatusPage":
        return cls(logger)

    @classmethod
    def standalone_show_title(cls, settings: PngSettings) -> bool:
        return settings.HUD.tyres_status_show_title

    @final
    def setup_page(self):
        self.tyre_icon_uris: defaultdict[str, str] = load_tyre_icons_uri_dict()

        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            ref_row = get_ref_row(data)
            if not ref_row:
                self.set_qml_property("tyres", [])
                return

            telemetry_public = ref_row["driver-info"]["telemetry-setting"] == "Public"
            self.set_qml_property("telemetryDisabled", not telemetry_public)
            self.set_qml_property("tyres", self._build_tyres(ref_row["tyre-info"]) if telemetry_public else [])

    def _build_tyres(self, tyre_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """One dict per tyre in FL, FR, RL, RR order; a missing value is None."""
        wear = tyre_info.get("current-wear") or {}
        core_temps = tyre_info.get("inner-temps") or {}
        surface_temps = tyre_info.get("surface-temps") or {}
        # Subscript, not .get(): unmapped compounds need the defaultdict __missing__.
        icon = self.tyre_icon_uris[tyre_info.get("visual-tyre-compound", "UNKNOWN")]

        return [
            {
                "position": position,
                "compoundIcon": icon,
                "wear": wear.get(wear_key),
                "coreTemp": core_temps.get(temp_key),
                "surfaceTemp": surface_temps.get(temp_key),
            }
            for wear_key, temp_key, position in self.TYRES
        ]
