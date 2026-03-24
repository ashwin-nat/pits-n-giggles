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
class HudOverlayData(HighFreqBase):

    throttle: float
    brake: float
    rev_lights_pct: int
    rpm: int
    gear: int
    speed_kmph: int
    drs_enabled: bool
    drs_available: bool
    drs_distance: int
    ers_harv_mguk_j: float
    ers_deployed_j: float
    ers_rem_j: float
    ers_mode: str
    tl_warnings: int
    circuit_pos_m: int
    circuit: str
    track_temp: int
    air_temp: int
    g_force_lat: float
    g_force_long: float
    g_force_vert: float

    def __bool__(self) -> bool:
        return None not in (
            self.throttle,
            self.brake,
            self.rev_lights_pct,
            self.rpm,
            self.gear,
            self.speed_kmph,
            self.drs_enabled,
            self.drs_available,
            self.drs_distance,
            self.ers_harv_mguk_j,
            self.ers_deployed_j,
            self.ers_rem_j,
            self.ers_mode,
            self.tl_warnings,
            self.circuit_pos_m,
            self.circuit,
            self.track_temp,
            self.air_temp
            # G forces may be None if telemetry is disabled. Here we ignore them.
        )

    @classmethod
    def from_json(cls, json_data: dict) -> "HudOverlayData":
        hud_data = json_data["hud"]
        g_force_data = json_data["g-force"]
        pens_stats_data = json_data["penalties-and-stats"]
        return cls(
            throttle=hud_data["throttle"],
            brake=hud_data["brake"],
            rev_lights_pct=hud_data["rev-lights"],
            rpm=hud_data["rpm"],
            gear=hud_data["gear"],
            speed_kmph=hud_data["speed-kmph"],
            drs_enabled=hud_data["drs-enabled"],
            drs_available=hud_data["drs-available"],
            drs_distance=hud_data["drs-distance"],
            ers_harv_mguk_j=hud_data["ers-harv-mguk"],
            ers_deployed_j=hud_data["ers-deployed"],
            ers_rem_j=hud_data["ers-remaining"],
            ers_mode=hud_data["ers-mode"],
            tl_warnings=pens_stats_data["corner-cutting-warnings"],
            circuit_pos_m=hud_data["circuit-position"],
            circuit=json_data["circuit-enum-name"],
            g_force_lat=g_force_data["lat"],
            g_force_long=g_force_data["long"],
            g_force_vert=g_force_data["vert"],
            track_temp=pens_stats_data["track-temperature"],
            air_temp=pens_stats_data["air-temperature"],
        )

