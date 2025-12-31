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
from typing import Any, Dict, List, Optional, override, final
from pathlib import Path

from PySide6.QtQuick import QQuickItem
from PySide6.QtCore import Qt, QUrl, QObject
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlayWidget, BaseOverlayQML
from apps.hud.ui.overlays.mfd.pages import (BasePage, CollapsedPage, MfdPageBase,
                                            FuelInfoPage, LapTimesPage, TyreSetsPage,
                                            PitRejoinPredictionPage,
                                            TyreInfoPage, WeatherForecastPage)
from lib.config import PngSettings

from .animation import AnimatedStackedWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PageIndicatorFooter(QWidget):
    """Footer widget that displays page indicators as circles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)  # Increased height for more padding
        self.total_pages = 0
        self.active_page = 0
        self.circle_radius = 6  # Radius of each circle
        self.circle_spacing = 30  # Space between circle centers

    def set_page_count(self, count: int):
        """Set the total number of pages."""
        self.total_pages = count
        self.update()

    def set_active_page(self, index: int):
        """Set which page is currently active (0-indexed)."""
        self.active_page = index
        self.update()

    def paintEvent(self, _event):
        """Draw the page indicator circles and border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw top border
        painter.setPen(QPen(QColor(255, 255, 255), 0.4))
        painter.drawLine(0, 1, self.width(), 1)

        # Draw background
        painter.fillRect(0, 2, self.width(), self.height() - 2, QColor(0, 0, 0, 76))

        if self.total_pages == 0:
            return

        # Calculate total width needed for all circles
        total_width = (self.total_pages - 1) * self.circle_spacing + 2 * self.circle_radius

        # Start position (centered horizontally)
        start_x = (self.width() - total_width) // 2
        center_y = self.height() // 2

        # Draw each circle
        for i in range(self.total_pages):
            center_x = start_x + self.circle_radius + i * self.circle_spacing

            if i == self.active_page:
                # Filled white circle for active page
                painter.setPen(QPen(QColor(245, 236, 235), 1))
                painter.setBrush(QBrush(QColor(245, 236, 235)))
            else:
                # Unfilled white outline for inactive pages
                painter.setPen(QPen(QColor(245, 236, 235), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.drawEllipse(
                center_x - self.circle_radius,
                center_y - self.circle_radius,
                self.circle_radius * 2,
                self.circle_radius * 2
            )

class MfdOverlayOld(BaseOverlayWidget):

    OVERLAY_ID = "mfd"
    PAGES: List[BasePage] = [
        CollapsedPage,
        FuelInfoPage,
        LapTimesPage,
        PitRejoinPredictionPage,
        TyreInfoPage,
        WeatherForecastPage,
        TyreSetsPage,
    ]
    PAGE_CLS_BY_KEY = {page.KEY: page for page in PAGES}

    def __init__(self,
                 config: OverlaysConfig,
                 settings: PngSettings,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool
                 ):

        self.mfdClosed = 40
        self.settings = settings
        super().__init__(config, logger, locked, opacity, scale_factor, windowed_overlay)

        # Always start collapsed, but keep width & position
        geo = self.geometry()
        self.setGeometry(geo.x(), geo.y(), geo.width(), self.mfdClosed)

        # Initialize handlers and start on default/collapsed page
        self._init_cmd_handlers()

    def build_ui(self):
        """Set up stacked pages and layout with footer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # No spacing between pages and footer

        self.pages = AnimatedStackedWidget(self)
        self.pages.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addWidget(self.pages)

        # Add footer with page indicators
        self.footer = PageIndicatorFooter(self)
        layout.addWidget(self.footer)

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

        # Initialize footer with page count
        self.footer.set_page_count(self.pages.count())
        self.footer.set_active_page(0)

        # Apply initial height constraint for collapsed page
        self.pages.setFixedHeight(self.mfdClosed)
    def _register_page(self, widget_cls: BasePage) -> None:
        """Register an MFD page"""
        self.logger.debug(f"{self.OVERLAY_ID} | Registering MFD page {widget_cls.KEY}")
        self.pages.addWidget(widget_cls(self, self.logger, self.scale_factor))

    def _init_cmd_handlers(self):
        """Register command handlers."""
        @self.on_event("next_page")
        def _handle_next_page(_data: Dict[str, Any]):
            self.logger.debug(f"{self.OVERLAY_ID} | Switching to next page...")

            # Step forward until we find a new index different from current
            current_index = self.pages.currentIndex()
            next_index = next(self.page_cycle)
            while next_index == current_index:
                next_index = next(self.page_cycle)

            # in unlocked mode, don't allow switching to collapsed page
            if not self.locked and next_index == 0:
                next_index = 1
                self.logger.debug(f"{self.OVERLAY_ID} | Unlocked mode. Skipping collapsed page in next_page")
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
            self.logger.debug(f'{self.OVERLAY_ID} | [OVERRIDDEN HANDLER] Setting locked state to {locked}')

            # We need to not be in the default/collapse page when unlocking, so that the user gets a sense of how much
            # width to configure.
            if not locked and self.pages.currentIndex() == 0:
                self.logger.debug(f"{self.OVERLAY_ID} | Switching to next page before unlocking ...")
                _handle_next_page(data)

            self.set_locked_state(locked)

        @self.on_event("set_config")
        def _handle_set_config(data: Dict[str, Any]):
            config = OverlaysConfig.fromJSON(data)
            self.logger.debug(f"{self.OVERLAY_ID} | [OVERRIDDEN HANDLER] Setting config {config}")
            self.set_window_position(config)
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
                self.logger.warning(f"{self.OVERLAY_ID} | Page {dest_index} not found")
                return
        active_page._handle_event(event_type, data)

    def _switch_page(self, old_index: int, new_index: int):
        """Switch page with animation and resize MFD based on open/closed state."""

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
        self.adjustSize()

        page_name = "collapsed" if new_index == 0 else "expanded"
        self.logger.debug(f"MFD: switched to {page_name} page")

        # Notify the new and old pages of the switch
        self._handle_event("page_active_status", {"active" : False}, old_index)
        self._handle_event("page_active_status", {"active" : True}, new_index)

    def _is_page_active(self, page: QWidget) -> bool:
        """Return True if the given page is currently active."""
        return self.pages.currentWidget() is page

    def _on_page_changed(self, index: int):
        """Ensure correct MFD height when a page changes (after animation)."""
        # Update footer indicator
        self.footer.set_active_page(index)

        if index == 0:
            # Collapsed state
            self.pages.setFixedHeight(self.mfdClosed)
            self.resize(self.width(), self.mfdClosed + self.footer.height())
            self.logger.debug(f"{self.OVERLAY_ID} | Page changed -> collapsed (height={self.mfdClosed})")
        else:
            # Expanded state
            self.pages.setMaximumHeight(16777215)  # Qt::QWIDGETSIZE_MAX
            self.pages.setMinimumHeight(0)
            self.adjustSize()

    @override
    def rebuild_ui(self):
        # Capture index only if pages already exists
        current_index = self.pages.currentIndex() if self.pages is not None else None

        # Reuse the existing rebuild
        super().rebuild_ui()

        # Restore page if valid
        if current_index is not None and 0 <= current_index < self.pages.count():
            self.pages.setCurrentIndex(current_index)
            self._on_page_changed(current_index)

class MfdOverlay(BaseOverlayQML):

    OVERLAY_ID = "mfd"
    QML_FILE: Path = Path(__file__).parent / "mfd.qml"

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

        super().__init__(
            config=config,
            logger=logger,
            locked=locked,
            opacity=opacity,
            scale_factor=scale_factor,
            windowed_overlay=windowed_overlay,
            refresh_interval_ms=None,
        )

        self._init_cmd_handlers()

    @final
    def _setup_window(self):
        super()._setup_window()

        # Example: build from user config
        enabled_pages = [
            CollapsedPage,
            FuelInfoPage,
            LapTimesPage,
            WeatherForecastPage,
            TyreSetsPage,
            # later: WeatherPage, TyrePage, etc
        ]

        for cls in enabled_pages:
            self._mfd_pages.append(cls(self, self.logger))
        self._current_index = 0

        # Set total pages in QML
        self._root.setProperty("totalPages", len(self._mfd_pages))
        self._root.setProperty("currentPageIndex", 0)

        self._apply_current_page()

    def _apply_current_page(self):
        try:
            page = self._mfd_pages[self._current_index]
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"{self.OVERLAY_ID} | Failed to apply current page: {e}")
            return
        qml_url = QUrl.fromLocalFile(str(page.QML_FILE.resolve()))

        is_collapsed = (page.KEY == CollapsedPage.KEY)

        self._root.setProperty("collapsed", is_collapsed)
        self._root.setProperty("currentPageQml", qml_url)
        self._root.setProperty("currentPageIndex", self._current_index)

        page.on_page_active()
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

        if not self._mfd_pages:
            return

        old = self._current_index
        self._current_index = (old + 1) % len(self._mfd_pages)

        self._apply_current_page()

        self.logger.debug(f"{self.OVERLAY_ID} | Page {old} -> {self._current_index}")

    @property
    def current_page_item(self) -> Optional[QQuickItem]:
        loader: Optional[QObject] = self._root.findChild(QObject, "pageLoader")
        if not loader:
            return None

        item = loader.property("item")
        return item if isinstance(item, QQuickItem) else None
