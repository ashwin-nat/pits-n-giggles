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
from typing import final

from PySide6.QtCore import QObject, QUrl

from apps.hud.ui.overlays.base.base_overlay import BaseOverlay
from apps.hud.ui.overlays.mfd.page_host import register_page_event_handlers
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import PngSettings
from lib.logger import PngLogger

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class StandalonePageHost(BaseOverlay):
    """Shows a single MFD page in its own always-on-top overlay window.

    Composition counterpart of MfdOverlay: where the MFD hosts N pages and cycles
    through them, this host wraps exactly one fully constructed MfdPageBase
    instance in standalone_wrapper.qml. Written once, never subclassed — any
    MFD page works standalone by being handed to this class.

    Responsibilities:
    - Window chrome: optional title bar (a window concern, not a page concern)
    - Page lifecycle: activates the page on the wrapper's Loader item
    - Event bridge: every event type the page handles is registered as an
      overlay command handler that forwards to the page
    - Stats: overlay stats plus the page's own stats under "__PAGE__"
    """

    QML_FILE: Path = Path(__file__).parent / "standalone_wrapper.qml"

    def __init__(
        self,
        page: MfdPageBase,
        settings: PngSettings,
        logger: PngLogger,
        show_title_bar: bool,
    ):
        self._page = page
        self._show_title_bar = show_title_bar
        # Identity comes from the hosted page (instance attribute shadows the
        # empty class attribute; set before super().__init__ asserts on it).
        self.OVERLAY_ID = page.OVERLAY_ID
        super().__init__(settings, logger)

    def _active_page(self) -> MfdPageBase:
        """The one page this host ever shows."""
        return self._page

    @final
    def post_setup(self):
        """Load the page QML into the wrapper, activate the page, bridge its events."""
        self.root.setProperty("pageSource", QUrl.fromLocalFile(str(self._page.PAGE_QML_FILE.resolve())))
        loader = self.root.findChild(QObject, "pageContent")
        assert loader is not None, f"{self._page.KEY} | standalone QML missing Loader with objectName 'pageContent'"
        page_item = loader.property("item")
        assert page_item is not None, f"{self._page.KEY} | Loader 'pageContent' item is None — page QML failed to load"
        self.root.setProperty("showTitleBar", self._show_title_bar)
        self.root.setProperty("titleText", page_item.property("title") or "")

        self._page._on_page_activated(page_item)

        register_page_event_handlers(self, [self._page], self._active_page)

    @final
    def get_stats(self) -> dict:
        """Overlay-level stats plus the hosted page's stats."""
        return {
            **super().get_stats(),
            "__PAGE__": self._page.get_stats(),
        }
