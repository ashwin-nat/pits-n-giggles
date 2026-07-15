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

from apps.hud.common import get_ers_mode_color
from apps.hud.ui.overlays.base import BaseOverlay
from lib.config import OverlayId, PngSettings
from lib.f1_types import CarStatusData
from lib.logger import PngLogger

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PuOverlay(BaseOverlay):

    # Remember to add the QML path to scripts/png.spec
    QML_FILE = Path(__file__).parent / "pu.qml"
    OVERLAY_ID = OverlayId.PU

    def __init__(self, settings: PngSettings, logger: PngLogger) -> None:
        self._show_harvest_info = settings.HUD.pu_display_harvest_info
        super().__init__(settings, logger)
        self._register_event_handlers()

    def _register_event_handlers(self):

        @self.on_event("stream_overlay_update")
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

            # - Derived values ----------------------
            total_w  = ice_w + mguk_w
            total_kw = total_w / 1000.0
            ice_frac  = ice_w  / total_w if total_w > 0 else 0.0
            mguk_frac = mguk_w / total_w if total_w > 0 else 0.0

            # - Harvest info -----------------------
            harv_pwr_mguk_w = pu_data["mguk-harv-power-w"]
            harv_pwr_mguh_w = pu_data["mguh-harv-power-w"]
            harv_nrg_mguk_j = hud_data["ers-harv-mguk"] or 0
            harv_nrg_mguh_j = hud_data["ers-harv-mguh"] or 0

            # - Push to QML ------------------------
            self.set_qml_property("totalPowerKw",  f"{total_kw:.1f} kW")
            self.set_qml_property("icePowerKw",    f"{ice_w  / 1000.0:.1f}")
            self.set_qml_property("mgukPowerKw",   f"{mguk_w / 1000.0:.1f}")
            self.set_qml_property("iceFraction",   ice_frac)
            self.set_qml_property("mgukFraction",  mguk_frac)
            self.set_qml_property("iceTempC",      ice_temp_c)
            self.set_qml_property("ersMode",       ers_mode)
            self.set_qml_property("ersColor",      ers_color)

            # - Harvest info push ------------------
            self.set_qml_property("showHarvestInfo", self._show_harvest_info)
            if self._show_harvest_info:
                harv_limit_mguk  = f1_26_data["harv-limit-j"] if is_f1_26 else CarStatusData.MAX_MGUK_HARV_PER_LAP
                mguk_harv_frac   = min(harv_nrg_mguk_j / harv_limit_mguk, 1.0)
                is_harvesting    = bool(harv_pwr_mguk_w)
                throttle         = hud_data["throttle"] or 0.0

                if mguk_harv_frac == 0:
                    prog_bar_str = "LIMIT REACHED"
                elif is_harvesting and throttle == 1.0 and is_f1_26:
                    prog_bar_str = "SUPER CLIPPING"
                elif is_harvesting:
                    prog_bar_str = "HARVESTING"
                else:
                    prog_bar_str = ""

                self.set_qml_property("isF126",           is_f1_26)
                self.set_qml_property("progBarStr",       prog_bar_str)
                self.set_qml_property("harvNrgMgukMj",    f"{harv_nrg_mguk_j / 1_000_000.0:.2f} MJ")
                self.set_qml_property("harvPwrMgukKw",    f"{harv_pwr_mguk_w / 1_000.0:.1f} kW")
                self.set_qml_property("mgukHarvFraction", mguk_harv_frac)
                self.set_qml_property("isHarvesting",     is_harvesting)
                if not is_f1_26:
                    self.set_qml_property("harvNrgMguhMj", f"{harv_nrg_mguh_j / 1_000_000.0:.2f} MJ")
                    self.set_qml_property("harvPwrMguhKw", f"{harv_pwr_mguh_w / 1_000.0:.1f} kW")
