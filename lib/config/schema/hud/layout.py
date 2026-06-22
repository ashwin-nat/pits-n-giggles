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

import copy
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field

from ..diff import ConfigDiffMixin

# ------------------------------------- CONSTANTS ----------------------------------------------------------------------

class OverlayId(str, Enum):
    LAP_TIMER        = "lap_timer"
    TIMING_TOWER     = "timing_tower"
    MFD              = "mfd"
    INPUT_TELEMETRY  = "input_telemetry"
    TRACK_RADAR      = "track_radar"
    HUD              = "hud_overlay"
    CIRCUIT_INFO     = "circuit_info"
    PU               = "pu"
    FUEL_INFO        = "fuel_info"
    TYRE_INFO        = "tyre_info"
    LAP_TIMES        = "lap_times_standalone"
    WEATHER          = "weather_standalone"
    PIT_REJOIN       = "pit_rejoin_standalone"
    TYRE_SETS        = "tyre_sets_standalone"
    PACE_COMP        = "pace_comp_standalone"
    TRAFFIC_MONITOR  = "traffic_monitor_standalone"

# -------------------------------------- MODELS ------------------------------------------------------------------------

class OverlayPosition(ConfigDiffMixin, BaseModel):
    """
    Screen position and scale for a single overlay.

    No validation is intentionally performed here.
    """
    x: int = Field(description="X position in pixels")
    y: int = Field(description="Y position in pixels")
    scale_factor: float = Field(default=1.0, description="UI scale factor (multiplier)")


    def toJSON(self) -> Dict:
        """Used for Qt signal/slot transport."""
        return {
            "x": self.x,
            "y": self.y,
            "scale_factor": self.scale_factor,
        }

    @classmethod
    def fromJSON(cls, json_dict: Dict) -> "OverlayPosition":
        """Used for Qt signal/slot transport."""
        return cls(
            x=json_dict["x"],
            y=json_dict["y"],
            scale_factor=json_dict.get("scale_factor", 1.0),
        )

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

DEFAULT_OVERLAY_LAYOUT: Dict[str, OverlayPosition] = {
    OverlayId.LAP_TIMER: OverlayPosition(
        x=600,
        y=60,
    ),
    OverlayId.TIMING_TOWER: OverlayPosition(
        x=10,
        y=55,
    ),
    OverlayId.MFD: OverlayPosition(
        x=10,
        y=355,
    ),
    OverlayId.INPUT_TELEMETRY: OverlayPosition(
        x=10,
        y=600,
    ),
    OverlayId.TRACK_RADAR: OverlayPosition(
        x=40,
        y=600,
    ),
    OverlayId.HUD: OverlayPosition(
        x=300,
        y=600,
    ),
    OverlayId.CIRCUIT_INFO: OverlayPosition(
        x=600,
        y=600,
    ),
    OverlayId.PU: OverlayPosition(
        x=600,
        y=120,
    ),
    # Standalone MFD pages — spread in two rows of 4 (each 400×220 at scale=1,
    # assuming 1920×1080; top row y=10, bottom row y=840).
    OverlayId.FUEL_INFO:       OverlayPosition(x=10,   y=10),
    OverlayId.TYRE_INFO:       OverlayPosition(x=420,  y=10),
    OverlayId.LAP_TIMES:       OverlayPosition(x=830,  y=10),
    OverlayId.WEATHER:         OverlayPosition(x=1240, y=10),
    OverlayId.PIT_REJOIN:      OverlayPosition(x=10,   y=840),
    OverlayId.TYRE_SETS:       OverlayPosition(x=420,  y=840),
    OverlayId.PACE_COMP:       OverlayPosition(x=830,  y=840),
    OverlayId.TRAFFIC_MONITOR: OverlayPosition(x=1240, y=840),
}

# -------------------------------------- HELPERS -----------------------------------------------------------------------

def merge_overlay_layout(
    user_layout: Optional[Dict[str, OverlayPosition]],
) -> Dict[str, OverlayPosition]:
    layout = copy.deepcopy(DEFAULT_OVERLAY_LAYOUT)

    if user_layout:
        for key, value in user_layout.items():
            layout[key] = value

    return layout
