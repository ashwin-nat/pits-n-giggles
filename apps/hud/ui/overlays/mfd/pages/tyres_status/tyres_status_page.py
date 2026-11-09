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
from typing import Any, Dict, final

from apps.hud.common import get_ref_row
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.assets_loader import load_tyre_icons_uri_dict
from lib.config import MfdPageId, OverlayId, PngSettings

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyresStatusPage(MfdPageBase):
    """Per-tyre wear, core temperature and surface temperature, plus the fitted compound, of the reference driver."""
    OVERLAY_ID = OverlayId.TYRES_STATUS
    KEY = MfdPageId.TYRES_STATUS
    PAGE_QML_FILE: Path = Path(__file__).parent / "tyres_status_page.qml"

    WEAR_DECIMALS = 1
    NO_DATA = float("-inf")  # sentinel for "no data"; QML checks isFinite()
    NO_AGE = -1              # tyreAge sentinel; QML hides the label when negative

    # (wear key, temp key, QML property prefix)
    TYRES = (
        ("front-left-wear", "fl", "fl"),
        ("front-right-wear", "fr", "fr"),
        ("rear-left-wear", "rl", "rl"),
        ("rear-right-wear", "rr", "rr"),
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
            tyre_info: Dict[str, Any] = ref_row.get("tyre-info") if ref_row else None
            telemetry_setting = ref_row.get("driver-info", {}).get("telemetry-setting") if ref_row else None
            if not tyre_info or telemetry_setting is None:
                self._clear()
                return

            # Subscript, not .get(): unmapped compounds need the defaultdict __missing__.
            self.set_qml_property("compoundIcon", self.tyre_icon_uris[tyre_info.get("visual-tyre-compound", "UNKNOWN")])

            self.set_qml_property("tyreAge", tyre_info["tyre-age"])

            telemetry_public = telemetry_setting == "Public"
            self.set_qml_property("telemetryDisabled", not telemetry_public)
            if not telemetry_public:
                self._clear_tyres()
                return

            wear = tyre_info.get("current-wear") or {}
            core_temps = tyre_info.get("inner-temps") or {}
            surface_temps = tyre_info.get("surface-temps") or {}
            for wear_key, temp_key, prefix in self.TYRES:
                self.set_qml_property(f"{prefix}Wear", self._round_wear(wear.get(wear_key)))
                self.set_qml_property(f"{prefix}CoreTemp", self._temp(core_temps.get(temp_key)))
                self.set_qml_property(f"{prefix}SurfaceTemp", self._temp(surface_temps.get(temp_key)))

    def _round_wear(self, value: Any) -> float:
        # Rounded here so sub-display changes hit the property cache instead of QML.
        return self.NO_DATA if value is None else round(float(value), self.WEAR_DECIMALS)

    def _temp(self, value: Any) -> float:
        return self.NO_DATA if value is None else float(value)

    def _clear_tyres(self) -> None:
        for _, _, prefix in self.TYRES:
            for suffix in ("Wear", "CoreTemp", "SurfaceTemp"):
                self.set_qml_property(f"{prefix}{suffix}", self.NO_DATA)

    def _clear(self) -> None:
        self.set_qml_property("compoundIcon", "")
        self.set_qml_property("tyreAge", self.NO_AGE)
        self.set_qml_property("telemetryDisabled", False)
        self._clear_tyres()
