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

# pylint: disable-all

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.infra.high_freq_types import InputTelemetryData
from apps.hud.ui.overlays.base import BaseOverlayQML
from PySide6.QtCore import QMetaObject, Qt

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class InputTelemetryOverlay(BaseOverlayQML):
    """
    Track map overlay that displays an SVG representation of the current circuit.

    - Loads appropriate SVG based on circuit name
    - Displays the track map in the QML window
    - Updates when circuit changes
    """

    QML_FILE = Path(__file__).parent / "input_telemetry.qml"
    OVERLAY_ID = "input_telemetry"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int, scale_factor: float, windowed_overlay: bool):
        logger.debug(f"{self.OVERLAY_ID} | InputTelemetryOverlay initialized. Path={self.QML_FILE}. exists={self.QML_FILE.is_file()}")
        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor, windowed_overlay)
        self._init_handlers()

    def build_ui(self):
        """Initialize QML connection after window is set up."""
        pass

    def _init_handlers(self):

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):

            car_telemetry = data["car-telemetry"]
            throttle = car_telemetry["throttle"] # 0-100
            brake = car_telemetry["brake"] # 0-100
            steering = car_telemetry["steering"] # -100 to 100

            self.logger.debug(f'{self.overlay_id} | Received request "stream_overlay_update" . throttle={throttle}, brake={brake}, steering={steering}')

            # Send data to QML and trigger update
            if self._root:
                # Use invokeMethod to call QML function directly
                from PySide6.QtCore import Q_ARG
                QMetaObject.invokeMethod(
                    self._root,
                    "updateTelemetry",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG("QVariant", throttle),
                    Q_ARG("QVariant", brake),
                    Q_ARG("QVariant", steering)
                )

        @self.on_high_freq(InputTelemetryData.__hf_type__)
        def _handle_input_telemetry(data: InputTelemetryData):
            self.logger.info(f'{self.overlay_id} | Received throttle={data.throttle}, brake={data.brake}, steering={data.steering}')  # TDOO: remove

            # Send data to QML and trigger update
            # if self._root:
            #     # Use invokeMethod to call QML function directly
            #     from PySide6.QtCore import Q_ARG
            #     QMetaObject.invokeMethod(
            #         self._root,
            #         "updateTelemetry",
            #         Qt.ConnectionType.QueuedConnection,
            #         Q_ARG("QVariant", data.throttle),
            #         Q_ARG("QVariant", data.brake),
            #         Q_ARG("QVariant", data.steering)
            #     )