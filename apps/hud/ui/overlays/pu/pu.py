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
from typing import Optional

from apps.hud.common import get_ers_mode_color
from apps.hud.ui.overlays.base import BaseOverlay
from lib.config import OverlayId, OverlayPosition

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PuOverlay(BaseOverlay):

    # Remember to add the QML path to scripts/png.spec
    QML_FILE = Path(__file__).parent / "pu.qml"
    OVERLAY_ID = OverlayId.PU

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
        show_harvest_info: bool,
    ) -> None:

        self._show_harvest_info = show_harvest_info
        super().__init__(
            config=config,
            logger=logger,
            locked=locked,
            opacity=opacity,
            scale_factor=scale_factor,
            windowed_overlay=windowed_overlay,
            refresh_interval_ms=None,
        )

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
            harv_nrg_mguk_j = hud_data["ers-harv-mguk"]
            harv_nrg_mguh_j = hud_data["ers-harv-mguh"]

            # - Push to QML ------------------------
            self.set_qml_property("totalPowerKw",  round(total_kw,       1))
            self.set_qml_property("icePowerKw",    round(ice_w  / 1000.0, 1))
            self.set_qml_property("mgukPowerKw",   round(mguk_w / 1000.0, 1))
            self.set_qml_property("iceFraction",   round(ice_frac,  2))
            self.set_qml_property("mgukFraction",  round(mguk_frac, 2))
            self.set_qml_property("iceTempC",      ice_temp_c)
            self.set_qml_property("ersMode",       ers_mode)
            self.set_qml_property("ersColor",      ers_color)
