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
from typing import Any, Dict, TYPE_CHECKING

from PySide6.QtQuick import QQuickItem

from apps.hud.common import get_ref_row, is_race_type_session
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.f1_types import F1Utils

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class FuelInfoPage(MfdPageBase):
    KEY = "fuel_info"
    QML_FILE: Path = Path(__file__).parent / "fuel_page.qml"

    MIN_FUEL = 0.2

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        super().__init__(overlay, logger)
        self._init_handlers()

    def _init_handlers(self):
        @self.on_event("race_table_update")
        def update(data: Dict[str, Any]) -> None:
            """Update fuel information display."""
            ref_row = get_ref_row(data)
            if not ref_row:
                return

            root = self.root
            if not self.root:
                self.logger.error(f"{self.KEY} | Failed to find root")
                return

            page_item = self._page_item
            if not page_item:
                return

            if ref_row["driver-info"]["telemetry-setting"] != "Public":
                self._set_all_dim(root)
                return

            session_type = data["event-type"]
            fuel = ref_row["fuel-info"]

            page_item.setProperty("lastValue", self._fmt(fuel.get("last-lap-fuel-used")))

            if is_race_type_session(session_type):
                page_item.setProperty("currValue", self._fmt(fuel.get("curr-fuel-rate")))
                page_item.setProperty("tgtAvgValue", self._fmt(fuel.get("target-fuel-rate-average")))
                page_item.setProperty("tgtNextValue", self._fmt(fuel.get("target-fuel-rate-next-lap")))
                surplus = fuel.get("surplus-laps-png")
            else:
                page_item.setProperty("currValue", "---")
                page_item.setProperty("tgtAvgValue", "---")
                page_item.setProperty("tgtNextValue", "---")
                surplus = fuel.get("surplus-laps-game")

            if surplus is not None:
                page_item.setProperty(
                    "surplusText",
                    f"Surplus: {F1Utils.formatFloat(surplus, precision=3, signed=True)} laps"
                )
                page_item.setProperty("surplusValue", surplus)
                page_item.setProperty("surplusValid", True)
            else:
                page_item.setProperty("surplusText", "Surplus: ---")
                page_item.setProperty("surplusValid", False)

    def _fmt(self, value):
        return f"{value:.3f}" if value is not None else "---"

    def _set_all_dim(self, page_item: QQuickItem) -> None:
        for prop in ("currValue", "lastValue", "tgtAvgValue", "tgtNextValue"):
            page_item.setProperty(prop, "---")
        page_item.setProperty("surplusText", "Surplus: ---")
        page_item.setProperty("surplusValid", False)
