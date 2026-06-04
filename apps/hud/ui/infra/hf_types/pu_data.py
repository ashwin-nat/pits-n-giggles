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

from dataclasses import dataclass
from .base import HighFreqBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class PowerUnitOverlayData(HighFreqBase):

    ice_power_output_w: float
    mguk_power_output_w: float
    ice_temp_c: float
    ers_harv_mguk_j: float
    ers_harv_mguh_j: float
    ers_deployed_j: float
    ers_rem_j: float
    ers_mode: str
    ers_harv_limit_j: float
    f1_26_enabled: bool
    ot_active: bool

    def __bool__(self) -> bool:
        return None not in (
            self.ice_power_output_w,
            self.mguk_power_output_w,
            self.ice_temp_c,
            self.ers_harv_mguk_j,
            self.ers_harv_mguh_j,
            self.ers_deployed_j,
            self.ers_rem_j,
            self.ers_mode,
            self.ers_harv_limit_j,
            self.f1_26_enabled,
            self.ot_active
        )

    @classmethod
    def from_json(cls, json_data: dict) -> "PowerUnitOverlayData":
        hud_data = json_data["hud"]
        pu_data  = json_data["power-unit"]
        f1_26_data =json_data["2026-regs-info"]

        return cls(
            ice_power_output_w=pu_data["ice-power-output-w"],
            mguk_power_output_w=pu_data["mguk-power-output-w"],
            ice_temp_c=pu_data["ice-temp-c"],
            ers_harv_mguk_j=hud_data["ers-harv-mguk"],
            ers_harv_mguh_j=hud_data["ers-harv-mguh"],
            ers_deployed_j=hud_data["ers-deployed"],
            ers_rem_j=hud_data["ers-remaining"],
            ers_mode=hud_data["ers-mode"],
            ers_harv_limit_j=f1_26_data["harv-limit-j"],
            f1_26_enabled=f1_26_data["2026-regs-enabled"],
            ot_active=f1_26_data["overtake-active"],
        )

    @property
    def speed_mph(self) -> int:
        return round(self.speed_kmph * 0.621371)
