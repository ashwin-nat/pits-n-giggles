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
from typing import Any, Dict, final

from apps.hud.common import get_ref_row, is_race_type_session
from apps.hud.ui.overlays.mfd.pages.standalone_base import \
    StandalonePageOverlay
from lib.config import MfdPageId, OverlayId, OverlaysFuelEstimationMode
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class FuelInfoPage(StandalonePageOverlay):
    OVERLAY_ID = OverlayId.FUEL_INFO
    KEY = MfdPageId.FUEL_INFO
    PAGE_QML_FILE: Path = Path(__file__).parent / "fuel_page.qml"

    MIN_FUEL = 0.2

    def __init__(self, config, logger, locked, opacity, scale_factor, windowed_overlay,
                 show_title_bar,
                 fuel_est_mode: OverlaysFuelEstimationMode):
        self.fuel_est_mode = fuel_est_mode
        super().__init__(config, logger, locked, opacity, scale_factor, windowed_overlay, show_title_bar)

    def _configure(self, fuel_est_mode: OverlaysFuelEstimationMode) -> None:  # pylint: disable=arguments-differ
        self.fuel_est_mode = fuel_est_mode

    @final
    def setup_overlay(self):

        @self.on_page_event("race_table_update")
        def update(data: Dict[str, Any]) -> None:
            """Update fuel information display."""
            ref_row = get_ref_row(data)
            if not ref_row:
                return

            if ref_row["driver-info"]["telemetry-setting"] != "Public":
                self._set_all_dim()
                return

            session_type = data["event-type"]
            fuel = ref_row["fuel-info"]

            self.set_qml_property("lastValue", self._fmt(fuel.get("last-lap-fuel-used")))

            if is_race_type_session(session_type):
                self.set_qml_property("currValue", self._fmt(fuel.get("curr-fuel-rate")))
                self.set_qml_property("tgtAvgValue", self._fmt(fuel.get("target-fuel-rate-average")))
                self.set_qml_property("tgtNextValue", self._fmt(fuel.get("target-fuel-rate-next-lap")))
                if self.fuel_est_mode == OverlaysFuelEstimationMode.LINEAR_REGRESSION:
                    surplus = fuel.get("surplus-laps-png")
                else:
                    surplus = fuel.get("surplus-laps-game")
            else:
                self.set_qml_property("currValue", "---")
                self.set_qml_property("tgtAvgValue", "---")
                self.set_qml_property("tgtNextValue", "---")
                surplus = fuel.get("surplus-laps-game")

            if surplus is not None:
                self.set_qml_property(
                    "surplusText",
                    f"Surplus: {F1Utils.formatFloat(surplus, precision=3, signed=True)} laps"
                )
                self.set_qml_property("surplusValue", surplus)
                self.set_qml_property("surplusValid", True)
            else:
                self.set_qml_property("surplusText", "Surplus: ---")
                self.set_qml_property("surplusValid", False)

    def _fmt(self, value):
        return f"{value:.3f}" if value is not None else "---"

    def _set_all_dim(self) -> None:
        for prop in ("currValue", "lastValue", "tgtAvgValue", "tgtNextValue"):
            self.set_qml_property(prop, "---")
        self.set_qml_property("surplusText", "Surplus: ---")
        self.set_qml_property("surplusValid", False)
