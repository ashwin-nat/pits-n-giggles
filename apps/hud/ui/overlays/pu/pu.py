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
from typing import final

from apps.hud.common import get_ers_mode_color
from apps.hud.ui.overlays.mfd.pages.standalone_base import StandalonePageOverlay
from lib.config import MfdPageId, OverlayId

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PuOverlay(StandalonePageOverlay):

    # Remember to add the QML path to scripts/png.spec
    OVERLAY_ID = OverlayId.PU
    KEY = MfdPageId.PU_INFO
    PAGE_QML_FILE: Path = Path(__file__).parent / "pu.qml"

    @final
    def setup_overlay(self):

        @self.on_page_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: dict):
            hud_data    = data["hud"]
            pu_data     = data["power-unit"]
            f1_26_data  = data["2026-regs-info"]

            # ERS values
            is_f1_26 = f1_26_data["2026-regs-enabled"]
            ers_mode  = hud_data["ers-mode"]
            ot_active = f1_26_data["overtake-active"]
            ers_color = get_ers_mode_color(ers_mode, is_f1_26, ot_active)
            if ers_mode:
                ers_mode = ers_mode.upper()

                if is_f1_26 and ers_mode == "OVERTAKE" and not ot_active:
                    ers_mode = "BOOST"

            # Raw power values (watts)
            ice_w  = pu_data["ice-power-output-w"]
            mguk_w = pu_data["mguk-power-output-w"]
            ice_temp_c = pu_data["ice-temp-c"]

            # ── Derived values ─────────────────────────────────────────────
            total_w  = ice_w + mguk_w
            total_kw = total_w / 1000.0
            ice_frac  = ice_w  / total_w if total_w > 0 else 0.0
            mguk_frac = mguk_w / total_w if total_w > 0 else 0.0

            # ── Push to QML ────────────────────────────────────────────────
            self.set_qml_property("totalPowerKw",  round(total_kw,       1))
            self.set_qml_property("icePowerKw",    round(ice_w  / 1000.0, 1))
            self.set_qml_property("mgukPowerKw",   round(mguk_w / 1000.0, 1))
            self.set_qml_property("iceFraction",   round(ice_frac,  2))
            self.set_qml_property("mgukFraction",  round(mguk_frac, 2))
            self.set_qml_property("iceTempC",      ice_temp_c)
            self.set_qml_property("ersMode",       ers_mode)
            self.set_qml_property("ersColor",      ers_color)
