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

# Radar display constants (must match track_radar.qml)
_RADAR_RANGE_M   = 25.0   # metres represented by half the radar area
_RADAR_AREA_PX   = 255.0  # baseWidth * 0.85  (300 * 0.85)

def _car_px(formula_type: str) -> tuple[float, float]:
    """Return (width_px, length_px) scaled to the radar coordinate system."""
    dims = _CAR_DIMENSIONS_M.get(formula_type, _DEFAULT_CAR_DIMENSIONS_M)
    px_per_m = (_RADAR_AREA_PX / 2.0) / _RADAR_RANGE_M
    return round(dims.width_m * px_per_m, 1), round(dims.length_m * px_per_m, 1)

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
    def post_setup(self):
        """Set the opacity property when the window is ready."""
        self._set_base_opacity_property(self.opacity)
        self._set_idle_opacity_property(self.idle_opacity)

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

        # Calculate relative positions for all drivers
        driver_list = self._calculate_relative_positions(data, ref_driver)

        # Send data to QML and trigger update
        car_w_px, car_l_px = _car_px(data.formula_type)
        self.set_qml_property("carWidthPx", car_w_px)
        self.set_qml_property("carLengthPx", car_l_px)
        self.invoke_qml_method("updateTelemetry", driver_list)

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
        - name: driver name
        - team: team name
        - is_ref: whether this is the reference driver
        - relX: relative X position (right is positive)
        - relZ: relative Z position (forward is positive)
        - heading: heading angle in degrees relative to ref driver
        """
        driver_list = []

        # Get reference driver position and orientation
        ref_pos = ref_driver.car_motion.world_position
        ref_yaw = ref_driver.car_motion.orientation.yaw

        # Rotate to ref driver's coordinate system
        # In F1 games, typically X is right and Z is forward
        # We need forward to be up on the radar (Z axis)
        cos_yaw = math.cos(-ref_yaw)
        sin_yaw = math.sin(-ref_yaw)

        for driver in session.motion_data:
            if not driver.car_motion:
                # Can be none if the motion packet has not arrived by then
                continue
            # Get absolute position
            pos = driver.car_motion.world_position

            # Calculate vector from ref to this car in world space
            dx = pos.x - ref_pos.x
            dz = pos.z - ref_pos.z

            # Swap axes: use Z as the primary forward axis
            rel_x = dz * sin_yaw + dx * cos_yaw  # Right
            rel_z = dz * cos_yaw - dx * sin_yaw  # Forward

            # Calculate heading relative to ref driver
            driver_yaw = driver.car_motion.orientation.yaw
            rel_heading = math.degrees(driver_yaw - ref_yaw)

            driver_list.append({
                'name': driver.name,
                'team': driver.team,
                'is_ref': driver.is_ref,
                'relX': rel_x,
                'relZ': rel_z,
                'heading': rel_heading,
                'index': driver.index,
                'track_position': driver.track_position
            })

        return driver_list

    def _set_base_opacity_property(self, opacity: int):
        self.set_qml_property("baseOpacity", opacity / 100.0)

    def _set_idle_opacity_property(self, opacity: int):
        self.set_qml_property("idleOpacity", opacity / 100.0)

    def _set_locked_property(self, locked: bool):
        self.set_qml_property("lockedMode", locked)
