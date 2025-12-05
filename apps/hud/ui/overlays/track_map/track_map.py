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
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session,
                             is_tt_session)
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlayQML

import logging
from apps.hud.ui.infra.config import OverlaysConfig
from pathlib import Path

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TrackMapOverlay(BaseOverlayQML):
    """
    The smallest possible functional QML overlay.

    - Provides a QML file
    - Implements build_ui() (required by BaseOverlay)
    - Does NOT display anything
    - Prevents crashes during startup
    """

    QML_FILE = Path(__file__).parent / "track_map.qml"
    OVERLAY_ID = "track_map"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int, scale_factor: float, windowed_overlay: bool):
        logger.debug(f"{self.OVERLAY_ID} | TrackMapOverlay initialized. Path={self.QML_FILE}. exists={self.QML_FILE.is_file()}")
        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor, windowed_overlay)
        self._init_handlers()

    def build_ui(self):
        """Nothing to build yet – just required by abstract class."""
        pass

    def _init_handlers(self):

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):

            self.logger.debug(f"{self.OVERLAY_ID} | Received stream_overlay_update event")
