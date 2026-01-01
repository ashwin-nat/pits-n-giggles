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
from typing import Any, Dict, List, Optional, final

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQuick import QQuickItem

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlayQML
from apps.hud.ui.overlays.mfd.pages import (CollapsedPage, FuelInfoPage,
                                            LapTimesPage, MfdPageBase,
                                            PitRejoinPredictionPage,
                                            TyreInfoPage, TyreSetsPage,
                                            WeatherForecastPage)
from lib.config import PngSettings

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdOverlay(BaseOverlayQML):

    OVERLAY_ID = "mfd"
    QML_FILE: Path = Path(__file__).parent / "mfd.qml"

    PAGES: List[MfdPageBase] = [
        CollapsedPage,
        FuelInfoPage,
        LapTimesPage,
        PitRejoinPredictionPage,
        TyreInfoPage,
        WeatherForecastPage,
        TyreSetsPage,
    ]
    PAGE_CLS_BY_KEY = {page.KEY: page for page in PAGES}

    def __init__(
        self,
        config: OverlaysConfig,
        settings: PngSettings,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
    ):
        # Pages are created AFTER QML is loaded
        self._mfd_pages: List[MfdPageBase] = []
        self._current_index = 0
        self._init_pages_order(settings)

        super().__init__(
            config=config,
            logger=logger,
            locked=locked,
            opacity=opacity,
            scale_factor=scale_factor,
            windowed_overlay=windowed_overlay,
            refresh_interval_ms=None, # Telemetry based refreshes
        )

        self._register_page_event_handlers()
        self._init_cmd_handlers()

    def _register_page_event_handlers(self):
        """Automatically register all event handlers from all pages."""
        # Collect all unique event types from all pages
        all_event_types = set()
        for page in self._mfd_pages:
            all_event_types.update(page.get_handled_event_types())

        # Register a handler for each event type that broadcasts to all pages
        for event_type in all_event_types:
            self._register_broadcast_handler(event_type)

        self.logger.debug("%s | Registered %d event handlers %s", self.OVERLAY_ID, len(all_event_types), all_event_types)

    def _register_broadcast_handler(self, event_type: str):
        """Register a handler that broadcasts an event to all interested pages."""
        @self.on_event(event_type)
        def _handler(data: Dict[str, Any]):
            # Broadcast to all pages that handle this event
            for page in self._mfd_pages:
                if page.handles_event(event_type):
                    page.handle_event(event_type, data)

    def _init_pages_order(self, settings: PngSettings):
        """Initialize the order of the enabled pages in the MFD."""
        self.enabled_pages = [
            {"key": "collapsed", "cls": CollapsedPage, "position": 0},
            *[
                {
                    "key": key,
                    "cls": self.PAGE_CLS_BY_KEY[key],
                    "position": settings.position
                }
                for key, settings in
                settings.HUD.mfd_settings.sorted_enabled_pages()
            ]
        ]

    @final
    def _setup_window(self):
        """Load QML and extract the root QQuickWindow. Init the pages in the specified order"""
        super()._setup_window()
        self._root.pageLoaded.connect(self._on_page_loaded)

        for page_info in self.enabled_pages:
            cls = page_info["cls"]
            self._mfd_pages.append(cls(self, self.logger))
        self._current_index = 0

        # Set total pages in QML
        self._root.setProperty("totalPages", len(self._mfd_pages))
        self._root.setProperty("currentPageIndex", 0)

        self._apply_current_page()

    def _on_page_loaded(self, page_key: str, item: QQuickItem):
        """Called when a page is loaded completely"""
        page = self.PAGE_CLS_BY_KEY.get(page_key)
        if not page:
            self.logger.debug("Ignoring stale load for %s", page_key)
            return

        # Qt guarantees order of delivery, but it doesn't change the fact that the request for page change
        # and actual page load are asynchronous
        # If pages are cycled very quickly, this class's tracker may be well ahead of the actual qml load status
        # Simplest fix, deactivate everything else except current
        for page in self._mfd_pages:
            if page.KEY == page_key:
                page.on_page_activated(item)
            elif page.is_active:
                page.on_page_deactivated()

    def _apply_current_page(self):
        """Apply the current page."""
        try:
            page = self._mfd_pages[self._current_index]
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"{self.OVERLAY_ID} | Failed to apply current page: {e}")
            return
        qml_url = QUrl.fromLocalFile(str(page.QML_FILE.resolve()))

        is_collapsed = (page.KEY == CollapsedPage.KEY)

        self._root.setProperty("collapsed", is_collapsed)
        self._root.setProperty("activePageKey", page.KEY)
        self._root.setProperty("currentPageQml", qml_url)
        self._root.setProperty("currentPageIndex", self._current_index)

        self.logger.debug(
            "%s | Applied page '%s' (index=%d, collapsed=%s)",
            self.OVERLAY_ID,
            page.KEY,
            self._current_index,
            is_collapsed,
        )

    def _init_cmd_handlers(self):
        """Register command handlers."""
        @self.on_event("next_page")
        def _handle_next_page(_data: Dict[str, Any]):
            self._next_page()

        @self.on_event("race_table_update")
        def _handle_race_update(data: Dict[str, Any]):
            self._handle_event("race_table_update", data)

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            self._handle_event("stream_overlay_update", data)

        @self.on_event("set_locked_state")
        def _handle_set_locked_state(data: Dict[str, Any]):
            locked = data.get('new-value', False)
            self.logger.debug(f'{self.OVERLAY_ID} | [OVERRIDDEN HANDLER] Setting locked state to {locked}')

            # We need to not be in the default/collapse page when unlocking, so that the user gets a sense of how much
            # width to configure.
            if not locked and self._current_index == 0:
                self.logger.debug(f"{self.OVERLAY_ID} | Switching to next page before unlocking ...")
                _handle_next_page(data)

            self.set_locked_state(locked)

    def _handle_event(self, event_type: str, data: Dict[str, Any], dest_index: Optional[int] = None) -> None:
        """Forward event to page.

        Args:
            event_type (str): Event type
            data (Dict[str, Any]): Event data
            dest_index (Optional[int]): Destination page index. If not specified, the current page is used.
        """
        if not self._mfd_pages:
            return

        if dest_index is None:
            index = self._current_index
        else:
            if dest_index < 0 or dest_index >= len(self._mfd_pages):
                self.logger.warning(f"{self.OVERLAY_ID} | Page index {dest_index} out of range")
                return
            index = dest_index

        page = self._mfd_pages[index]
        page.handle_event(event_type, data)

    def _next_page(self):
        """Go to the next page in MFD overlay"""
        if not self._mfd_pages:
            return

        old = self._current_index
        self._current_index = (old + 1) % len(self._mfd_pages)

        self._apply_current_page()
        self.logger.debug(f"{self.OVERLAY_ID} | Page {old} -> {self._current_index}")

    @property
    def current_page_item(self) -> Optional[QQuickItem]:
        """Get the current page item."""
        loader: Optional[QObject] = self._root.findChild(QObject, "pageLoader")
        if not loader:
            return None

        item = loader.property("item")
        return item if isinstance(item, QQuickItem) else None
