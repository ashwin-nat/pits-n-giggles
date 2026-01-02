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

from typing import Dict

from pydantic import BaseModel, Field

# ------------------------------------- CONSTANTS ----------------------------------------------------------------------

LAP_TIMER_OVERLAY_ID = "lap_timer"
TIMING_TOWER_OVERLAY_ID = "timing_tower"
MFD_OVERLAY_ID = "mfd"
TRACK_MAP_OVERLAY_ID = "track_map"
INPUT_TELEMETRY_OVERLAY_ID = "input_telemetry"
TRACK_RADAR_OVERLAY_ID = "track_radar"

# -------------------------------------- MODELS ------------------------------------------------------------------------

class OverlayPosition(BaseModel):
    """
    Screen position for a single overlay.

    No validation is intentionally performed here.
    """
    x: int = Field(description="X position in pixels")
    y: int = Field(description="Y position in pixels")


    def toJSON(self) -> Dict[str, int]:
        """Used for Qt signal/slot transport."""
        return {
            "x": self.x,
            "y": self.y,
        }

    @classmethod
    def fromJSON(cls, json_dict: Dict[str, int]) -> "OverlayPosition":
        """Used for Qt signal/slot transport."""
        return cls(
            x=json_dict["x"],
            y=json_dict["y"],
        )

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

DEFAULT_OVERLAY_LAYOUT: Dict[str, OverlayPosition] = {
    LAP_TIMER_OVERLAY_ID: OverlayPosition(
        x=600,
        y=60,
    ),
    TIMING_TOWER_OVERLAY_ID: OverlayPosition(
        x=10,
        y=55,
    ),
    MFD_OVERLAY_ID: OverlayPosition(
        x=10,
        y=355,
    ),
    # TRACK_MAP_OVERLAY_ID: OverlayPosition(
    #     x=10,
    #     y=600,
    # ),
    INPUT_TELEMETRY_OVERLAY_ID: OverlayPosition(
        x=10,
        y=600,
    ),
    TRACK_RADAR_OVERLAY_ID: OverlayPosition(
        x=40,
        y=600,
    ),
}
