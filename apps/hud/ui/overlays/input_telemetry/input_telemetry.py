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
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, Qt

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.infra.hf_types import InputTelemetryData
from apps.hud.ui.overlays.base import BaseOverlayQML

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

    def __init__(self,
                 config: OverlaysConfig,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool):

        super().__init__(config, logger, locked, opacity, scale_factor, windowed_overlay)
        self._init_handlers()

    def build_ui(self):
        """Initialize QML connection after window is set up."""
        pass

    def _init_handlers(self):
        """Initialize event handlers."""
        @self.on_high_freq(InputTelemetryData.__hf_type__)
        def _handle_input_telemetry(data: InputTelemetryData):

            # Send data to QML and trigger update
            if self._root:
                # Use invokeMethod to call QML function directly
                QMetaObject.invokeMethod(
                    self._root,
                    "updateTelemetry",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG("QVariant", data.throttle),
                    Q_ARG("QVariant", data.brake),
                    Q_ARG("QVariant", data.steering),
                    Q_ARG("QVariant", data.rev_pct),
                )
