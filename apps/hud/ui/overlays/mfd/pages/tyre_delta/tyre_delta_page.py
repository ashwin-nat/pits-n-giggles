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
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QFont, QFontMetrics

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session)
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from apps.hud.ui.overlays.timing_tower.race_table import RaceTimingTable

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreDeltaPage(BasePage):
    """Tyre Delta page."""
    KEY = "tyre_delta"

    def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
        """Initialise the tyre delta prediction page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
            scale_factor (float): Scale factor
        """
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="TYRE DELTA")
        self._build_ui()
        self._init_event_handlers()

    def _build_ui(self):
        """Build the UI"""
        pass

    def _init_event_handlers(self):
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            """Update the page with new data.

            Args:
                data (Dict[str, Any]): The incoming data from the server (top level, including all keys)
            """
            self.logger.debug(f"{self.overlay_id} | Received stream overlay update")
