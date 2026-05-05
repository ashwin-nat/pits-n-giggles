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

import math

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QRadialGradient
from PySide6.QtQml import QQmlImageProviderBase
from PySide6.QtQuick import QQuickImageProvider

from ._radar_math import _RADAR_AREA_PX, _RADAR_BASE_WIDTH

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _make_glow_image(is_left: bool, car_w_px: float, car_l_px: float) -> QImage:
    """
    Generate a single _RADAR_BASE_WIDTH x _RADAR_BASE_WIDTH glow sector image for the left or right side.

    Replicates the Canvas atan2-based pie sector with a radial gradient:
      centre → 0.8 alpha, 30% out → 0.4 alpha, edge → 0.0 alpha.
    The image is generated once at base resolution; scaleFactor is handled
    by the GPU Scale transform on the parent Item.
    """
    size = _RADAR_BASE_WIDTH
    half_r = _RADAR_AREA_PX / 2.0
    cx = cy = size / 2.0
    half_w = car_w_px / 2.0
    half_l = car_l_px / 2.0

    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(0, 0, 0, 0))

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    grad = QRadialGradient(cx, cy, half_r)
    grad.setColorAt(0.0,  QColor(255, 0, 0, int(0.8 * 255)))
    grad.setColorAt(0.3,  QColor(255, 0, 0, int(0.4 * 255)))
    grad.setColorAt(1.0,  QColor(255, 0, 0, 0))
    painter.setBrush(grad)
    painter.setPen(Qt.PenStyle.NoPen)

    # Mirror the Canvas atan2 angles exactly.
    # Canvas: left glow arc from angleTopRight to angleBottomRight (clockwise).
    #   angleTopRight    = atan2(-halfL,  halfW)   →  upper-right of car = left side of radar
    #   angleBottomRight = atan2( halfL,  halfW)   →  lower-right of car
    # Canvas: right glow arc from angleBottomLeft to angleTopLeft (clockwise).
    #   angleTopLeft     = atan2(-halfL, -halfW)
    #   angleBottomLeft  = atan2( halfL, -halfW)
    # QPainter.drawPie uses 1/16° units, 0° = 3 o'clock, counter-clockwise positive.
    # Convert from Canvas (radians, CW from 3 o'clock) to QPainter (1/16°, CCW from 3 o'clock).
    rect_x = int(cx - half_r)
    rect_y = int(cy - half_r)
    rect_size = int(half_r * 2)

    # Both wedges are the same angular width; just differ in which side of the circle.
    # half_angle is the half-angle of the narrow wedge (e.g. ~70° for F1 car dims).
    half_angle_deg = math.degrees(math.atan2(half_l, half_w))

    if is_left:
        # Narrow wedge centred on 0° (3 o'clock = right side of radar)
        qt_start = int(-half_angle_deg * 16)
        qt_span  = int( half_angle_deg * 2 * 16)
    else:
        # Narrow wedge centred on 180° (9 o'clock = left side of radar)
        qt_start = int((180 - half_angle_deg) * 16)
        qt_span  = int( half_angle_deg * 2 * 16)

    painter.drawPie(rect_x, rect_y, rect_size, rect_size, qt_start, qt_span)
    painter.end()
    return img

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class RadarGlowImageProvider(QQuickImageProvider):
    """Serves pre-baked left/right glow sector images to QML via image://radar/glow-left|glow-right."""

    def __init__(self, car_w_px: float, car_l_px: float):
        super().__init__(QQmlImageProviderBase.ImageType.Image)
        self._images = {
            "glow-left":  _make_glow_image(True,  car_w_px, car_l_px),
            "glow-right": _make_glow_image(False, car_w_px, car_l_px),
        }

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:  # pylint: disable=unused-argument
        return self._images.get(image_id, QImage())
