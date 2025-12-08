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

            self.logger.debug(f'{self.overlay_id} | Received request "stream_overlay_update"')
