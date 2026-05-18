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
from typing import Any, Dict, Optional, final

from apps.hud.ui.infra.hf_types import DriverMotionInfo, LiveSessionMotionInfo
from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayId, OverlayPosition

from ._glow_provider import RadarGlowImageProvider
from ._radar_math import _RADAR_AREA_RATIO, _RADAR_RANGE_M, car_px, to_radar_coords

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
        car_w_px, car_l_px = car_px("F1 Modern")
        self.qml_engine.addImageProvider("radar", RadarGlowImageProvider(car_w_px, car_l_px))

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

        car_w_px, car_l_px = car_px(data.formula_type)
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

            radar_x, radar_y = to_radar_coords(rel_x, rel_z)
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
