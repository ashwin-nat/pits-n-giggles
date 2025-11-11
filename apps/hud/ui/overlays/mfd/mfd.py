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
import itertools
from typing import Any, Dict, Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QStackedWidget

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from lib.f1_types import F1Utils

from apps.hud.ui.overlays.mfd.pages import LapTimesPage, CollapsedPage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdOverlay(BaseOverlay):

    OVERLAY_ID = "mfd"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int):
        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity)
        self.mfdClosed = 40
        self.mfdOpen = 300

        self._init_cmd_handlers()

    def build_ui(self):
        """Set up stacked pages and layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget(self)
        layout.addWidget(self.pages)

        # Define pages
        self.collapsed_page = CollapsedPage(self)
        self.lap_times_page = LapTimesPage(self)

        # Add to stacked widget
        self.pages.addWidget(self.collapsed_page)
        self.pages.addWidget(self.lap_times_page)

        # Create page iterator (cycle)
        self.page_cycle = itertools.cycle(range(self.pages.count()))
        self.current_index = 0
        self.pages.setCurrentIndex(self.current_index)

    def _init_cmd_handlers(self):
        @self.on_command("next_page")
        def handle_next_page(_data: Dict[str, Any]):
            self.logger.debug(f"{self.overlay_id} | Switching to next page...")
            next_index = next(self.page_cycle)
            # Ensure we actually move to a *different* page each time
            if next_index == self.current_index:
                next_index = next(self.page_cycle)
            self.switch_page(next_index)

        @self.on_command("race_table_update")
        def handle_race_update(data: Dict[str, Any]):
            pass
            # if self.current_index == 1:
            #     self.lap_times_page.update_data(data.get("lap_data", []))

        @self.on_command("stream_overlay_update")
        def handle_stream_overlay_update(data: Dict[str, Any]):
            if self.current_index == 1:
                self.lap_times_page.update_data(data)

    def switch_page(self, index: int):
        """Switch page and resize MFD based on open/closed state."""
        self.logger.debug(f"MFD: switching to page {index}")
        self.current_index = index
        self.pages.setCurrentIndex(index)

        # Adjust height
        target_height = self.mfdClosed if index == 0 else self.mfdOpen
        self.resize(self.width(), target_height)
        self.logger.debug(
            f"MFD: resized to {'collapsed' if index == 0 else 'expanded'} height ({target_height})"
        )

    def clear(self):
        pass
