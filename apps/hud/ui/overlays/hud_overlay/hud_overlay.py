# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from typing import final, Optional
from apps.hud.ui.infra.hf_types import HudOverlayData

from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayPosition, HUD_OVERLAY_ID
from lib.track_segment_info.types import CornerSegmentInfo

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HudOverlay(BaseOverlayQML):
    """
    Extremely minimal QML overlay template.

    - Loads QML
    - Shows window
    """

    # Remember to update the spec file with the new QML path
    QML_FILE = Path(__file__).parent / "hud_overlay.qml"
    OVERLAY_ID = HUD_OVERLAY_ID

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
        refresh_interval_ms: Optional[int] = None,  # Set none for event-driven rendering (low frequency)
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

        self.subscribe_hf(HudOverlayData)

    ## For high frequency data, register HF types in ctor and render periodically in render_frame.
    @final
    def render_frame(self):
        """
        This will be called by the base class periodically based on the refresh rate specified in the ctor.
        Get the latest HF data and render it in the window
        """
        data = self.get_latest_hf_data(HudOverlayData)
        if not data:
            return

        corner_info = CornerSegmentInfo(
            segment_id=1,
            corner_number=1,
            corner_name="La Source",
        )

        # Ignore the rival field in the obj

        # Pedals (0.0–1.0 → 0–100)
        self.set_qml_property("throttleValue", data.throttle * 100.0)
        self.set_qml_property("brakeValue",    data.brake    * 100.0)

        # Rev lights / powertrain
        self.set_qml_property("revLightsPct", data.rev_lights_pct)
        self.set_qml_property("rpm",          data.rpm)
        self.set_qml_property("gear",         data.gear)
        self.set_qml_property("speedKmph",    data.speed_kmph)

        # DRS
        self.set_qml_property("drsEnabled",   data.drs_enabled)
        self.set_qml_property("drsAvailable", data.drs_available)
        self.set_qml_property("drsDistance",  min(data.drs_distance, 250))

        # ERS — all values as percentages
        #   Store / deploy limit = 4 MJ  |  MGU-K harvest limit = 2 MJ
        _STORE_J = 4_000_000.0
        _HARV_J  = 2_000_000.0
        self.set_qml_property("ersRemPct",      round(min(data.ers_rem_j       / _STORE_J * 100.0, 100.0), 1))
        self.set_qml_property("ersHarvPct",     round(min(data.ers_harv_mguk_j / _HARV_J  * 100.0, 100.0), 1))
        self.set_qml_property("ersDeployedPct", round(min(data.ers_deployed_j  / _STORE_J * 100.0, 100.0), 1))
        self.set_qml_property("ersMode",        data.ers_mode)
        self.set_qml_property("tlWarnings",     data.tl_warnings)
        self.set_qml_property("trackTempC",     data.track_temp)
        self.set_qml_property("airTempC",       data.air_temp)

        # Turn info (hardcoded placeholder — real lookup to be wired later)
        self.set_qml_property("turnNumber", corner_info.corner_number)
        self.set_qml_property("turnName",   corner_info.corner_name or "")
