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

from typing import NamedTuple

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

class _CarDims(NamedTuple):
    width_m: float
    length_m: float

# Real-world car dimensions keyed by formula type string
_CAR_DIMENSIONS_M: dict[str, _CarDims] = {
    "F1 Modern":      _CarDims(2.00, 5.63),
    "F1 Classic":     _CarDims(2.00, 5.63),
    "F1 Generic":     _CarDims(2.00, 5.63),
    "F1 World":       _CarDims(2.00, 5.63),
    "F1 Elimination": _CarDims(2.00, 5.63),
    "Esports":        _CarDims(2.00, 5.63),
    "F2":             _CarDims(1.90, 5.285),
    "F2 2021":        _CarDims(1.90, 5.285),
}
_DEFAULT_CAR_DIMENSIONS_M = _CarDims(2.00, 5.63)

# Radar display constants — single source of truth for both Python and QML.
# QML reads radarAreaRatio via a property set in post_setup so the canvas
# geometry and the Python coordinate projection always agree.
_RADAR_RANGE_M    = 25.0   # metres represented by half the radar area
_RADAR_BASE_WIDTH = 300    # must match baseWidth in track_radar.qml
_RADAR_AREA_RATIO = 0.85   # must match the 0.85 factor in track_radar.qml
_RADAR_AREA_PX    = _RADAR_BASE_WIDTH * _RADAR_AREA_RATIO

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def car_px(formula_type: str) -> tuple[float, float]:
    """Return (width_px, length_px) scaled to the radar coordinate system."""
    dims = _CAR_DIMENSIONS_M.get(formula_type, _DEFAULT_CAR_DIMENSIONS_M)
    px_per_m = (_RADAR_AREA_PX / 2.0) / _RADAR_RANGE_M
    return round(dims.width_m * px_per_m, 1), round(dims.length_m * px_per_m, 1)


def to_radar_coords(rel_x: float, rel_z: float) -> tuple[float, float]:
    # Match legacy QML projection exactly:
    #   radarArea.center + local offset where radarArea was inset in 300x300 root.
    # This resolves to root center while keeping radarArea-sized scaling.
    center = _RADAR_BASE_WIDTH / 2
    scale = (_RADAR_AREA_PX / 2) / _RADAR_RANGE_M
    return center - rel_x * scale, center - rel_z * scale
