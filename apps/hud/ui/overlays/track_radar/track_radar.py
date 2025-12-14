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

from PySide6.QtCore import Q_ARG, QMetaObject, Qt

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.infra.hf_types import LiveSessionMotionInfo, DriverMotionInfo
from apps.hud.ui.overlays.base import BaseOverlayQML

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TrackRadarOverlay(BaseOverlayQML):
    """
    Track radar overlay that displays all cars relative to the reference driver.

    - Centers the radar on the reference driver
    - Shows all other cars with their relative positions and headings
    - Updates in real-time with motion data
    """

    QML_FILE = Path(__file__).parent / "track_radar.qml"
    OVERLAY_ID = "track_radar"

    def __init__(self,
                 config: OverlaysConfig,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool):

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor, windowed_overlay)
        self._init_handlers()

    def build_ui(self):
        """Initialize QML connection after window is set up."""
        pass

    def _init_handlers(self):
        """Initialize event handlers."""
        @self.on_high_freq(LiveSessionMotionInfo.__hf_type__)
        def _handle_session_motion_info(data: LiveSessionMotionInfo):

            ref_driver = self._get_reference_driver(data)
            if not ref_driver:
                self.logger.debug(f"{self.OVERLAY_ID} | No reference driver found")
                return

            # Calculate relative positions for all drivers
            driver_list = self._calculate_relative_positions(data, ref_driver)

            # Send data to QML and trigger update
            if self._root:
                QMetaObject.invokeMethod(
                    self._root,
                    "updateTelemetry",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG("QVariant", driver_list)
                )

    def _get_reference_driver(self, session: LiveSessionMotionInfo) -> DriverMotionInfo | None:
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

        for driver in session.motion_data:
            # Get absolute position
            pos = driver.car_motion.world_position

            # Calculate vector from ref to this car in world space
            dx = pos.x - ref_pos.x
            dz = pos.z - ref_pos.z

            # Rotate to ref driver's coordinate system
            # In F1 games, typically X is right and Z is forward
            # We need forward to be up on the radar (Z axis)
            cos_yaw = math.cos(-ref_yaw)
            sin_yaw = math.sin(-ref_yaw)

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
