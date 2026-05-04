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
import math
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, final

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QRadialGradient
from PySide6.QtQml import QQmlImageProviderBase
from PySide6.QtQuick import QQuickImageProvider

from apps.hud.ui.infra.hf_types import DriverMotionInfo, LiveSessionMotionInfo
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayId, OverlayPosition

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

def _car_px(formula_type: str) -> tuple[float, float]:
    """Return (width_px, length_px) scaled to the radar coordinate system."""
    dims = _CAR_DIMENSIONS_M.get(formula_type, _DEFAULT_CAR_DIMENSIONS_M)
    px_per_m = (_RADAR_AREA_PX / 2.0) / _RADAR_RANGE_M
    return round(dims.width_m * px_per_m, 1), round(dims.length_m * px_per_m, 1)


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


class _RadarGlowImageProvider(QQuickImageProvider):
    """Serves pre-baked left/right glow sector images to QML via image://radar/glow-left|glow-right."""

    def __init__(self, car_w_px: float, car_l_px: float):
        super().__init__(QQmlImageProviderBase.ImageType.Image)
        self._images = {
            "glow-left":  _make_glow_image(True,  car_w_px, car_l_px),
            "glow-right": _make_glow_image(False, car_w_px, car_l_px),
        }

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:  # pylint: disable=unused-argument
        return self._images.get(image_id, QImage())


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TrackRadarOverlay(BaseOverlayQML):
    """
    Track radar overlay that displays all cars relative to the reference driver.

    - Centers the radar on the reference driver
    - Shows all other cars with their relative positions and headings
    - Updates in real-time with motion data
    """

    QML_FILE = Path(__file__).parent / "track_radar.qml"
    OVERLAY_ID = OverlayId.TRACK_RADAR

    def __init__(self,
                 config: OverlayPosition,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool,
                 refresh_interval_ms: int,
                 idle_opacity: int,):

        assert refresh_interval_ms
        self.idle_opacity = idle_opacity
        super().__init__(config, logger, locked, opacity, scale_factor, windowed_overlay, refresh_interval_ms)
        self.subscribe_hf(LiveSessionMotionInfo)
        self._register_handlers()

    @final
    def pre_setup(self):
        """Register the glow image provider before QML loads."""
        car_w_px, car_l_px = _car_px("F1 Modern")
        self.qml_engine.addImageProvider("radar", _RadarGlowImageProvider(car_w_px, car_l_px))

    @final
    def post_setup(self):
        """Set the opacity property when the window is ready."""
        self._set_base_opacity_property(self.opacity)
        self._set_idle_opacity_property(self.idle_opacity)
        self.set_qml_property("radarAreaRatio", _RADAR_AREA_RATIO)

    @final
    def set_opacity(self, opacity: int):
        """Set opacity."""
        self.logger.debug('%s | [OVERRIDDEN HANDLER] Setting opacity to %s', self.OVERLAY_ID, opacity)
        super().set_opacity(opacity)
        self._set_base_opacity_property(opacity)

    @final
    def set_locked_state(self, locked: bool):
        """Set locked state."""
        self.logger.debug('%s | [OVERRIDDEN HANDLER] Setting locked state to %s', self.OVERLAY_ID, locked)
        super().set_locked_state(locked)
        self._set_locked_property(locked)

    def _register_handlers(self):
        @self.on_event("set_track_radar_idle_opacity")
        def _handle_set_track_radar_idle_opacity(data: Dict[str, Any]):
            """Set track radar idle opacity."""
            self.logger.debug('%s | Received "set_track_radar_idle_opacity" event. Opacity: %s', self.OVERLAY_ID, data)
            opacity = data["opacity"]
            self.idle_opacity = opacity
            self._set_idle_opacity_property(opacity)

    @final
    def render_frame(self):
        """Render a new frame."""
        data = self.get_latest_hf_data(LiveSessionMotionInfo)
        if not data:
            return

        ref_driver = self._get_reference_driver(data)
        if not ref_driver or not ref_driver.car_motion:
            return

        car_w_px, car_l_px = _car_px(data.formula_type)
        self.set_qml_property("carWidthPx", car_w_px)
        self.set_qml_property("carLengthPx", car_l_px)

        driver_list = self._calculate_relative_positions(data, ref_driver)
        cars_nearby, car_on_left, car_on_right, car_data = self._compute_radar_frame(driver_list)

        self.set_qml_property("carsNearby", cars_nearby)
        self.set_qml_property("carOnLeft",  car_on_left)
        self.set_qml_property("carOnRight", car_on_right)
        self.set_qml_property("carData",    car_data)

    def _compute_radar_frame(self, driver_list: list) -> tuple[bool, bool, bool, list]:
        """Compute per-frame radar state from relative driver positions."""
        cars_nearby = False
        car_on_left = False
        car_on_right = False
        car_data: list = []

        for d in driver_list:
            if d['is_ref']:
                continue
            rel_x = d['relX']
            rel_z = d['relZ']
            dist = math.hypot(rel_x, rel_z)

            if dist <= _RADAR_RANGE_M:
                cars_nearby = True
            if self._is_car_on_left(rel_x, rel_z):
                car_on_left = True
            if self._is_car_on_right(rel_x, rel_z):
                car_on_right = True

            radar_x, radar_y = self._to_radar_coords(rel_x, rel_z)
            # Preserve pre-rewrite visual heading convention from QML:
            # old delegate used `rotation: -(driver.heading || 0)`.
            car_data.extend([radar_x, radar_y, -d['heading'], dist <= _RADAR_RANGE_M])

        return cars_nearby, car_on_left, car_on_right, car_data

    @staticmethod
    def _is_car_on_left(rel_x: float, rel_z: float) -> bool:
        return -4.0 < rel_x < -1.5 and abs(rel_z) < 8.0

    @staticmethod
    def _is_car_on_right(rel_x: float, rel_z: float) -> bool:
        return 1.5 < rel_x < 4.0 and abs(rel_z) < 8.0

    @staticmethod
    def _to_radar_coords(rel_x: float, rel_z: float) -> tuple[float, float]:
        # Match legacy QML projection exactly:
        #   radarArea.center + local offset where radarArea was inset in 300x300 root.
        # This resolves to root center while keeping radarArea-sized scaling.
        center = _RADAR_BASE_WIDTH / 2
        scale = (_RADAR_AREA_PX / 2) / _RADAR_RANGE_M
        return center - rel_x * scale, center - rel_z * scale

    def _get_reference_driver(self, session: LiveSessionMotionInfo) -> Optional[DriverMotionInfo]:
        """Get the reference driver from session data."""
        return next(
            (driver for driver in session.motion_data if driver.is_ref),
            None
        )

    def _calculate_relative_positions(self,
                                     session: LiveSessionMotionInfo,
                                     ref_driver: DriverMotionInfo) -> list[dict]:
        """
        Calculate relative positions of all drivers to the reference driver.

        Returns a list of dictionaries with:
        - is_ref: whether this is the reference driver
        - relX: relative X position (right is positive)
        - relZ: relative Z position (forward is positive)
        - heading: heading angle in degrees relative to ref driver
        """
        driver_list = []

        ref_pos = ref_driver.car_motion.world_position
        ref_yaw = ref_driver.car_motion.orientation.yaw

        cos_yaw = math.cos(-ref_yaw)
        sin_yaw = math.sin(-ref_yaw)

        for driver in session.motion_data:
            if not driver.car_motion:
                # Can be none if the motion packet has not arrived by then
                continue
            pos = driver.car_motion.world_position

            dx = pos.x - ref_pos.x
            dz = pos.z - ref_pos.z

            # Swap axes: use Z as the primary forward axis
            rel_x = dz * sin_yaw + dx * cos_yaw  # Right
            rel_z = dz * cos_yaw - dx * sin_yaw  # Forward

            driver_yaw = driver.car_motion.orientation.yaw
            rel_heading = math.degrees(driver_yaw - ref_yaw)

            driver_list.append({
                'is_ref': driver.is_ref,
                'relX': rel_x,
                'relZ': rel_z,
                'heading': rel_heading,
            })

        return driver_list

    def _set_base_opacity_property(self, opacity: int):
        self.set_qml_property("baseOpacity", opacity / 100.0)

    def _set_idle_opacity_property(self, opacity: int):
        self.set_qml_property("idleOpacity", opacity / 100.0)

    def _set_locked_property(self, locked: bool):
        self.set_qml_property("lockedMode", locked)
