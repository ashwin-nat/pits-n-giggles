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
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayId, OverlayPosition
from lib.f1_types.packet_7_car_status_data import CarStatusData

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PuOverlay(BaseOverlayQML):

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
        refresh_interval_ms: Optional[int] = None,
    ) -> None:

        super().__init__(
            config=config,
            logger=logger,
            locked=locked,
            opacity=opacity,
            scale_factor=scale_factor,
            windowed_overlay=windowed_overlay,
            refresh_interval_ms=refresh_interval_ms,
        )

        self._register_event_handlers()

    def _register_event_handlers(self):

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: dict):
            hud_data    = data.get("hud", {})
            pu_data     = data.get("power-unit", {})
            f1_26_data  = data.get("2026-regs-info", {})

            # Raw power values (watts)
            ice_w  = float(pu_data.get("ice-power-output-w")  or 0)
            mguk_w = float(pu_data.get("mguk-power-output-w") or 0)
            ice_temp_c = int(pu_data.get("ice-temp-c") or 0)

            # ERS energy values (joules)
            ers_harv_mguk_j = float(hud_data.get("ers-harv-mguk") or 0)
            ers_harv_mguh_j = float(hud_data.get("ers-harv-mguh") or 0)
            ers_deployed_j  = float(hud_data.get("ers-deployed")  or 0)
            ers_rem_j       = float(hud_data.get("ers-remaining")  or 0)
            ers_mode        = str(hud_data.get("ers-mode") or "")

            # 2026 fields
            harv_limit_j  = float(f1_26_data.get("harv-limit-j")      or 0)
            f1_26_enabled = bool(f1_26_data.get("2026-regs-enabled",   False))
            ot_active     = bool(f1_26_data.get("overtake-active",     False))

            # ── Derived values ─────────────────────────────────────────────
            total_w  = ice_w + mguk_w
            total_kw = total_w / 1000.0
            ice_frac  = ice_w  / total_w if total_w > 0 else 0.0
            mguk_frac = mguk_w / total_w if total_w > 0 else 0.0

            _store = CarStatusData.MAX_ERS_STORE_ENERGY
            ers_rem_pct = min(ers_rem_j / _store * 100.0, 100.0) if _store > 0 else 0.0

            # Deploy % — in 2026 mode there is no per-lap deploy cap
            if f1_26_enabled:
                deploy_pct = 100.0
            else:
                deploy_pct = min(ers_deployed_j / _store * 100.0, 100.0) if _store > 0 else 0.0

            # Harvest % — MGU-H counts only in 2026 mode
            if f1_26_enabled:
                harv_total_j = ers_harv_mguk_j + ers_harv_mguh_j
                harv_limit   = harv_limit_j if harv_limit_j > 0 else 1.0
            else:
                harv_total_j = ers_harv_mguk_j
                harv_limit   = CarStatusData.MAX_MGUK_HARV_PER_LAP
            harv_pct = min(harv_total_j / harv_limit * 100.0, 100.0) if harv_limit > 0 else 0.0

            # ── Push to QML ────────────────────────────────────────────────
            self.set_qml_property("totalPowerKw",  round(total_kw,       2))
            self.set_qml_property("icePowerKw",    round(ice_w  / 1000.0, 2))
            self.set_qml_property("mgukPowerKw",   round(mguk_w / 1000.0, 2))
            self.set_qml_property("iceFraction",   round(ice_frac,  4))
            self.set_qml_property("mgukFraction",  round(mguk_frac, 4))
            self.set_qml_property("ersRemPct",     round(ers_rem_pct, 1))
            self.set_qml_property("deployPct",     round(deploy_pct,  1))
            self.set_qml_property("harvestPct",    round(harv_pct,    1))
            self.set_qml_property("ersMode",       ers_mode)
            self.set_qml_property("ersModeColor",  get_ers_mode_color(ers_mode, f1_26_enabled, ot_active))
            self.set_qml_property("iceTempC",      ice_temp_c)
            self.set_qml_property("f1_26Enabled",  f1_26_enabled)
            self.set_qml_property("otActive",      ot_active)
