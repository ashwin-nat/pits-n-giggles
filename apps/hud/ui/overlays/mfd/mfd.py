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

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type, final

from PySide6.QtCore import QUrl
from PySide6.QtQuick import QQuickItem

from apps.hud.ui.overlays.base.base_overlay import BaseOverlay
from apps.hud.ui.overlays.mfd.page_host import register_page_event_handlers
from apps.hud.ui.overlays.mfd.pages import (CollapsedPage, FuelInfoPage,
                                            LapTimesPage, MfdPageBase,
                                            PaceCompPage,
                                            PitRejoinPredictionPage,
                                            TrafficMonitorPage, TyreInfoPage,
                                            TyreSetsPage, WeatherForecastPage)
from lib.config import OverlayId, PngSettings
from lib.logger import PngLogger

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdOverlay(BaseOverlay):

    OVERLAY_ID = OverlayId.MFD
    QML_FILE: Path = Path(__file__).parent / "mfd.qml"

    PAGES: ClassVar[List[Type[MfdPageBase]]] = [
        CollapsedPage,
        FuelInfoPage,
        LapTimesPage,
        PitRejoinPredictionPage,
        TyreInfoPage,
        WeatherForecastPage,
        TyreSetsPage,
        PaceCompPage,
        TrafficMonitorPage,
    ]
    PAGE_CLS_BY_KEY = {page.KEY: page for page in PAGES}

    def __init__(self, settings: PngSettings, logger: PngLogger):
        # Pages are created AFTER QML is loaded (post_setup), but from_settings() needs
        # settings again at that point, so it's kept around until then.
        self._settings = settings
        self._mfd_pages: List[MfdPageBase] = []
        self._current_index = 0
        self._init_pages_order(settings)

        super().__init__(settings, logger)

        register_page_event_handlers(self, self._mfd_pages, self._active_page)
        self._init_cmd_handlers()

    def _active_page(self) -> Optional[MfdPageBase]:
        """The page the carousel is currently showing, or None before pages exist."""
        if not self._mfd_pages:
            return None
        return self._mfd_pages[self._current_index]

    def _init_pages_order(self, settings: PngSettings):
        """Initialize the order of the enabled pages in the MFD."""
        self.enabled_pages: List[Type[MfdPageBase]] = [
            CollapsedPage,
            *[
                self.PAGE_CLS_BY_KEY[key]
                for key, _ in settings.HUD.mfd_settings.sorted_enabled_pages()
            ]
        ]

    @final
    def post_setup(self):
        """Init pages and QML properties after the window is ready."""
        self.root.pageLoaded.connect(self._on_page_loaded)

        for cls in self.enabled_pages:
            self._mfd_pages.append(cls.from_settings(self._settings, self.logger))
        self._current_index = 0

        # Set total pages in QML
        self.set_qml_property("totalPages", len(self._mfd_pages))
        self.set_qml_property("currentPageIndex", 0)

        self._apply_current_page()

    def _on_page_loaded(self, page_key: str, item: QQuickItem):
        """Called when a page is loaded completely"""
        if not any(page.KEY == page_key for page in self._mfd_pages):
            # Validate against the enabled pages, not the all-pages map: a valid-but-disabled
            # key would otherwise pass this check and the sweep below would deactivate every
            # active page while activating nothing.
            self.logger.debug("Ignoring stale load for %s", page_key)
            return

        # Qt guarantees order of delivery, but it doesn't change the fact that the request for page change
        # and actual page load are asynchronous
        # If pages are cycled very quickly, this class's tracker may be well ahead of the actual qml load status
        # Simplest fix, deactivate everything else except current
        for page in self._mfd_pages:
            if page.KEY == page_key:
                page._on_page_activated(item)
                self._replay_page_state(page)
            elif page.is_active:
                page._on_page_deactivated()

    def _replay_page_state(self, page: MfdPageBase) -> None:
        """Redeliver the latest known snapshot for every topic the newly activated page
        handles, so cycling to a page shows fresh content immediately instead of whatever
        was last rendered (or nothing) until the next broadcast arrives.

        This is the page-switch counterpart of BaseOverlay's replay-on-show (C4): the MFD
        window itself never becomes hidden when cycling pages, so that path never fires here.
        """
        if self._window_manager is None:
            return
        for event_type in page.get_handled_event_types():
            data = self._window_manager.replay_state_topic(self.OVERLAY_ID, event_type)
            if data is None:
                continue
            try:
                page.dispatch_event(event_type, data["__payload__"])
            except Exception:  # pylint: disable=broad-exception-caught
                self.logger.exception(
                    "%s | Error replaying cached state for page '%s' topic '%s'",
                    self.OVERLAY_ID, page.KEY, event_type,
                )

    def _apply_current_page(self):
        """Apply the current page."""
        assert 0 <= self._current_index < len(self._mfd_pages), (
            f"{self.OVERLAY_ID} | current_index {self._current_index} out of range "
            f"for {len(self._mfd_pages)} pages"
        )
        page = self._mfd_pages[self._current_index]

        # Deactivate the outgoing page eagerly: currentPageQml flips below and the Loader
        # destroys its item immediately, so without this the outgoing page would keep
        # pointing at a dead item until the new page's pageLoaded fires. _on_page_loaded
        # still sweeps as belt-and-braces for the fast-cycling race it was written for.
        for other in self._mfd_pages:
            if other is not page and other.is_active:
                other._on_page_deactivated()

        qml_url = QUrl.fromLocalFile(str(page.PAGE_QML_FILE.resolve()))

        is_collapsed = (page.KEY == CollapsedPage.KEY)

        self.set_qml_property("collapsed", is_collapsed)
        self.set_qml_property("activePageKey", page.KEY)
        self.set_qml_property("currentPageQml", qml_url)
        self.set_qml_property("currentPageIndex", self._current_index)

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
            self._step_page(1)

        @self.on_event("prev_page")
        def _handle_prev_page(_data: Dict[str, Any]):
            self._step_page(-1)

    @final
    def set_locked_state(self, locked):
        self.logger.debug('%s | [OVERRIDDEN HANDLER] Setting locked state to %s', self.OVERLAY_ID, locked)

        # We need to not be in the default/collapse page when unlocking, so that the user gets a sense of how much
        # width to configure.
        if not locked and self._current_index == 0:
            self.logger.debug("%s | Switching to next page before unlocking ...", self.OVERLAY_ID)
            self._step_page(1)
        super().set_locked_state(locked)

    @final
    def get_stats(self) -> dict:
        """Get the base class level stats and page stats."""
        overlay_stats = super().get_stats()
        page_stats = {
            page.KEY: page.get_stats()
            for page in self._mfd_pages
        }
        return {
            **overlay_stats,
            "__PAGES__": page_stats,
        }

    def _step_page(self, delta: int):
        """Step the current page index by delta (wrapping) and apply it."""
        if not self._mfd_pages:
            self.logger.error("%s | MFD initialised with no pages!", self.OVERLAY_ID)
            return

        old = self._current_index
        self._current_index = (old + delta) % len(self._mfd_pages)

        self._apply_current_page()
        self.logger.debug("%s | Page %s -> %s", self.OVERLAY_ID, old, self._current_index)
