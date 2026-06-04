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

from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayId, OverlayPosition

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
            pu_data     = data.get("power-unit", {})

            # Raw power values (watts)
            ice_w  = float(pu_data.get("ice-power-output-w")  or 0)
            mguk_w = float(pu_data.get("mguk-power-output-w") or 0)
            ice_temp_c = int(pu_data.get("ice-temp-c") or 0)

            # ── Derived values ─────────────────────────────────────────────
            total_w  = ice_w + mguk_w
            total_kw = total_w / 1000.0
            ice_frac  = ice_w  / total_w if total_w > 0 else 0.0
            mguk_frac = mguk_w / total_w if total_w > 0 else 0.0

            # ── Push to QML ────────────────────────────────────────────────
            self.set_qml_property("totalPowerKw",  round(total_kw,       2))
            self.set_qml_property("icePowerKw",    round(ice_w  / 1000.0, 2))
            self.set_qml_property("mgukPowerKw",   round(mguk_w / 1000.0, 2))
            self.set_qml_property("iceFraction",   round(ice_frac,  4))
            self.set_qml_property("mgukFraction",  round(mguk_frac, 4))
            self.set_qml_property("iceTempC",      ice_temp_c)
