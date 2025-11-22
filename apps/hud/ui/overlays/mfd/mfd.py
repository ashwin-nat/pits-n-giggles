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

import itertools
import logging
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from apps.hud.ui.overlays.mfd.pages import (BasePage, CollapsedPage,
                                            FuelInfoPage, LapTimesPage,
                                            PitRejoinPredictionPage,
                                            TyreInfoPage, WeatherForecastPage)
from lib.config import PngSettings

from .animation import AnimatedStackedWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdOverlay(BaseOverlay):

    OVERLAY_ID = "mfd"
    PAGES: List[BasePage] = [
        CollapsedPage,
        FuelInfoPage,
        LapTimesPage,
        PitRejoinPredictionPage,
        TyreInfoPage,
        WeatherForecastPage,
    ]
    PAGE_CLS_BY_KEY = {page.KEY: page for page in PAGES}

    def __init__(self,
                 config: OverlaysConfig,
                 settings: PngSettings,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float):

        self.mfdClosed = 40
        self.settings = settings
        self.mfdOpen = config.height
        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity, scale_factor)

        # Always start collapsed, but keep width & position
        geo = self.geometry()
        self.setGeometry(geo.x(), geo.y(), geo.width(), self.mfdClosed)

        # Initialize handlers and start on default/collapsed page
        self._init_cmd_handlers()

    def build_ui(self):
        """Set up stacked pages and layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.pages = AnimatedStackedWidget(self)
        self.pages.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addWidget(self.pages)
        # Re-apply height rules after every animated page change
        self.pages.currentChanged.connect(self._on_page_changed)

        enabled_pages = [
            {"key": "collapsed", "cls": CollapsedPage, "position": 0},
            *[
                {
                    "key": key,
                    "cls": self.PAGE_CLS_BY_KEY[key],
                    "position": settings.position
                }
                for key, settings in self.settings.HUD.mfd_settings.sorted_enabled_pages()
            ]
        ]

        for page in sorted(enabled_pages, key=lambda p: p["position"]):
            self._register_page(page["cls"])

        # Build an opaque iterator that cycles indefinitely
        self.page_cycle = itertools.cycle(range(self.pages.count()))
        self.pages.setCurrentIndex(0)

        # Apply initial height constraint for collapsed page
        self.pages.setFixedHeight(self.mfdClosed)

    def _register_page(self, widget_cls: BasePage) -> None:
        """Register an MFD page"""
        self.pages.addWidget(widget_cls(self, self.logger))

    def _init_cmd_handlers(self):
        """Register command handlers."""
        @self.on_event("next_page")
        def _handle_next_page(_data: Dict[str, Any]):
            self.logger.debug(f"{self.overlay_id} | Switching to next page...")

            # Step forward until we find a new index different from current
            current_index = self.pages.currentIndex()
            next_index = next(self.page_cycle)
            while next_index == current_index:
                next_index = next(self.page_cycle)

            # in unlocked mode, don't allow switching to collapsed page
            if not self.locked and next_index == 0:
                next_index = 1
                self.logger.debug(f"{self.overlay_id} | Unlocked mode. Skipping collapsed page in next_page")
            self._switch_page(current_index, next_index)

        @self.on_event("race_table_update")
        def _handle_race_update(data: Dict[str, Any]):
            self._handle_event("race_table_update", data)

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            self._handle_event("stream_overlay_update", data)

        @self.on_event("set_locked_state")
        def _handle_set_locked_state(data: Dict[str, Any]):
            locked = data.get('new-value', False)
            self.logger.debug(f'{self.overlay_id} | [OVERRIDDEN METHOD] Setting locked state to {locked}')

            # We need to not be in the default/collapse page when unlocking, so that the user gets a sense of how much
            # width to configure.
            if not locked and self.pages.currentIndex() == 0:
                self.logger.debug(f"{self.overlay_id} | Switching to next page before unlocking ...")
                _handle_next_page(data)

            self.set_locked_state(locked)

        @self.on_event("set_config")
        def _handle_set_config(data: Dict[str, Any]):
            config = OverlaysConfig.fromJSON(data)
            self.logger.debug(f"{self.overlay_id} | [OVERRIDDEN METHOD] Setting config {self.config}")
            config = OverlaysConfig.fromJSON(data)
            self.setGeometry(config.x, config.y, config.width, config.height)
            current_index = self.pages.currentIndex()
            if current_index != 0:
                self._switch_page(current_index, 0)

    def _handle_event(self, event_type: str, data: Dict[str, Any], dest_index: Optional[int] = None) -> None:
        """Forward event to page.

        Args:
            event_type (str): Event type
            data (Dict[str, Any]): Event data
            dest_index (Optional[int]): Destination page index. If not specified, the current page is used.
        """
        if dest_index is None:
            active_page: BasePage = self.pages.currentWidget()
        else:
            active_page = self.pages.widget(dest_index)
            if not active_page:
                self.logger.warning(f"{self.overlay_id} | Page {dest_index} not found")
                return
        active_page._handle_event(event_type, data)

    def _switch_page(self, old_index: int, new_index: int):
        """Switch page with animation and resize MFD based on open/closed state."""
        target_height = self.mfdClosed if new_index == 0 else self.mfdOpen

        # First set the stacked widget height constraint
        if new_index == 0:
            self.pages.setFixedHeight(self.mfdClosed)
        else:
            # Remove fixed height constraint for expanded pages
            self.pages.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
            self.pages.setMinimumHeight(0)

        # Use animated transition instead of instant switch
        self.pages.setCurrentIndexAnimated(new_index)

        # Resize the window
        self.resize(self.width(), target_height)

        page_name = "collapsed" if new_index == 0 else "expanded"
        self.logger.debug(f"MFD: switched to {page_name} page (height={target_height})")

        # Notify the new and old pages of the switch
        self._handle_event("pace_active_status", {"active" : False}, old_index)
        self._handle_event("pace_active_status", {"active" : True}, new_index)

    def _is_page_active(self, page: QWidget) -> bool:
        """Return True if the given page is currently active."""
        return self.pages.currentWidget() is page

    def _on_page_changed(self, index: int):
        """Ensure correct MFD height when a page changes (after animation)."""
        if index == 0:
            # Collapsed state
            self.pages.setFixedHeight(self.mfdClosed)
            self.resize(self.width(), self.mfdClosed)
            self.logger.debug(f"{self.overlay_id} | Page changed -> collapsed (height={self.mfdClosed})")
        else:
            # Expanded state
            self.pages.setMaximumHeight(16777215)  # Qt::QWIDGETSIZE_MAX
            self.pages.setMinimumHeight(0)
            self.resize(self.width(), self.mfdOpen)
            self.logger.debug(f"{self.overlay_id} | Page changed -> expanded (height={self.mfdOpen})")

