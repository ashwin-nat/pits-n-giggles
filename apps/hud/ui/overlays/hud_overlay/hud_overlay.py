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

from apps.hud.common import get_ref_row, is_race_type_session, is_tt_session
from apps.hud.ui.infra.hf_types import HudOverlayData
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import (HudOverlayFuelEstimationMode, HudOverlaySpeedUnit,
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
        speed_unit: HudOverlaySpeedUnit = HudOverlaySpeedUnit.KMPH,
        fuel_estimation_mode: HudOverlayFuelEstimationMode = HudOverlayFuelEstimationMode.LINEAR_REGRESSION,
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
            HudOverlayFuelEstimationMode.LINEAR_REGRESSION: "surplus-laps-png",
            HudOverlayFuelEstimationMode.GAME_BUILT_IN: "surplus-laps-game",
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

        # Ignore the rival field in the obj

        # Pedals (0.0–1.0 → 0–100)
        self.set_qml_property("throttleValue", data.throttle * 100.0)
        self.set_qml_property("brakeValue",    data.brake    * 100.0)

        # Rev lights / powertrain
        self.set_qml_property("revLightsPct", data.rev_lights_pct)
        self.set_qml_property("rpm",          data.rpm)
        self.set_qml_property("gear",         data.gear)
        if self._speed_unit == HudOverlaySpeedUnit.MPH:
            self.set_qml_property("speedKmph",    round(data.speed_kmph * 0.621371))
            self.set_qml_property("speedUnitLabel", "mph")
        else:
            self.set_qml_property("speedKmph",    data.speed_kmph)
            self.set_qml_property("speedUnitLabel", "km/h")

        # DRS
        self.set_qml_property("drsEnabled",   data.drs_enabled)
        self.set_qml_property("drsAvailable", data.drs_available)
        self.set_qml_property("drsDistance",  min(data.drs_distance, 250))

        # ERS — all values as percentages
        _store = CarStatusData.MAX_ERS_STORE_ENERGY
        _harv  = CarStatusData.MAX_MGUK_HARV_PER_LAP
        self.set_qml_property("ersRemPct",      round(min(data.ers_rem_j       / _store * 100.0, 100.0), 1))
        self.set_qml_property("ersHarvPct",     round(min(data.ers_harv_mguk_j / _harv  * 100.0, 100.0), 1))
        self.set_qml_property("ersDeployedPct", round(min(data.ers_deployed_j  / _store * 100.0, 100.0), 1))
        self.set_qml_property("ersMode",        data.ers_mode)
        self.set_qml_property("tlWarnings",     data.tl_warnings)
        self.set_qml_property("trackTempC",     data.track_temp)
        self.set_qml_property("airTempC",       data.air_temp)

        # Fuel
        self.set_qml_property("surplusFuel", self._surplus_fuel)

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
