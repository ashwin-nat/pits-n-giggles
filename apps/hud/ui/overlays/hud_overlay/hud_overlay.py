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
from typing import Any, Dict, Optional, final

from apps.hud.common import get_ers_mode_color, get_ref_row, is_race_type_session, is_tt_session
from apps.hud.ui.infra.hf_types import HudOverlayData
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import (OverlaysFuelEstimationMode, OverlaysSpeedUnit,
                        OverlayId, OverlayPosition)
from lib.f1_types.packet_7_car_status_data import CarStatusData

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HudOverlay(BaseOverlayQML):
    """
    Extremely minimal QML overlay template.

    - Loads QML
    - Shows window
    """

    # Remember to update the spec file with the new QML path
    QML_FILE = Path(__file__).parent / "hud_overlay.qml"
    OVERLAY_ID = OverlayId.HUD

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
        refresh_interval_ms: Optional[int] = None,
        speed_unit: OverlaysSpeedUnit = OverlaysSpeedUnit.KMPH,
        fuel_estimation_mode: OverlaysFuelEstimationMode = OverlaysFuelEstimationMode.LINEAR_REGRESSION,
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

        self._speed_unit = speed_unit
        self.subscribe_hf(HudOverlayData)

        self._surplus_fuel: Optional[float] = None
        self._surplus_fuel_key: str = {
            OverlaysFuelEstimationMode.LINEAR_REGRESSION: "surplus-laps-png",
            OverlaysFuelEstimationMode.GAME_BUILT_IN: "surplus-laps-game",
        }.get(fuel_estimation_mode)
        self._register_event_handlers()

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

        # Pedals (0.0–1.0 → 0–100)
        self.set_qml_property("throttleValue", data.throttle * 100.0)
        self.set_qml_property("brakeValue",    data.brake    * 100.0)

        # Rev lights / powertrain
        self.set_qml_property("revLightsPct", data.rev_lights_pct)
        self.set_qml_property("rpm",          data.rpm)
        self.set_qml_property("gear",         data.gear)
        if self._speed_unit == OverlaysSpeedUnit.MPH:
            self.set_qml_property("speedKmph",    data.speed_mph)
            self.set_qml_property("speedUnitLabel", "mph")
        else:
            self.set_qml_property("speedKmph",    data.speed_kmph)
            self.set_qml_property("speedUnitLabel", "km/h")

        # DRS / active aero + overtake (2026)
        f26 = data.f1_26_data
        if f26.enabled:
            if f26.active_aero_mode == "STRAIGHT_MODE":
                drs_text    = "STRAIGHT"
                drs_enabled = True
                drs_dist    = 0
            else:
                drs_text    = "CORNER"
                drs_enabled = False
                drs_dist    = min(f26.active_aero_dist, 250)
            drs_avlb    = f26.active_aero_avlb
            ot_enabled  = f26.overtake_active
            ot_avlb     = f26.overtake_avlb
        else:
            drs_text, drs_enabled = "DRS", data.drs_enabled
            drs_dist    = min(data.drs_distance, 250)
            drs_avlb    = data.drs_available
            ot_enabled  = False
            ot_avlb     = False

        self.set_qml_property("drsText",      drs_text)
        self.set_qml_property("drsEnabled",   drs_enabled)
        self.set_qml_property("drsAvailable", drs_avlb)
        self.set_qml_property("drsDistance",  drs_dist)
        self.set_qml_property("pitLimiterEnabled", data.pit_limiter_enabled)

        # ERS — all values as percentages
        _store = CarStatusData.MAX_ERS_STORE_ENERGY
        if f26.enabled:
            _harv = f26.harv_limit_j
            ers_rem_pct     = round(min(data.ers_rem_j       / _store * 100.0, 100.0), 1)
            ers_harv_pct    = round(min(data.ers_harv_mguk_j / _harv  * 100.0, 100.0), 1)
            ers_dep_pct     = 100
        else:
            _harv  = CarStatusData.MAX_MGUK_HARV_PER_LAP
            ers_rem_pct     = round(min(data.ers_rem_j       / _store * 100.0, 100.0), 1)
            ers_harv_pct    = round(min(data.ers_harv_mguk_j / _harv  * 100.0, 100.0), 1)
            ers_dep_pct     = round(min(data.ers_deployed_j  / _store * 100.0, 100.0), 1)

        self.set_qml_property("ersRemPct", ers_rem_pct)
        self.set_qml_property("ersHarvPct", ers_harv_pct)
        self.set_qml_property("ersDeployedPct", ers_dep_pct)
        self.set_qml_property("ersMode",        data.ers_mode)
        self.set_qml_property("ersColor",       get_ers_mode_color(data.ers_mode, f26.enabled, f26.overtake_active))
        self.set_qml_property("tlWarnings",     data.tl_warnings)
        self.set_qml_property("trackTempC",     data.track_temp)
        self.set_qml_property("airTempC",       data.air_temp)

        # Fuel
        self.set_qml_property("surplusFuel", self._surplus_fuel)

        self.set_qml_property("isF126",      f26.enabled)
        self.set_qml_property("otEnabled",   ot_enabled)
        self.set_qml_property("otAvailable", ot_avlb)


    def _register_event_handlers(self):
        @self.on_event("race_table_update")
        def update(data: Dict[str, Any]) -> None:
            """Update fuel information display."""
            ref_row = get_ref_row(data)
            if not ref_row:
                return

            if ref_row["driver-info"]["telemetry-setting"] != "Public":
                self._surplus_fuel = None
                return

            session_type = data["event-type"]
            fuel = ref_row["fuel-info"]

            if is_race_type_session(session_type):
                self._surplus_fuel = fuel.get(self._surplus_fuel_key)
            elif is_tt_session(session_type):
                self._surplus_fuel = fuel.get("surplus-laps-game")
