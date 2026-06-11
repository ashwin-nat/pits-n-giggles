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

from PySide6.QtQuick import QQuickItem

from apps.hud.ui.overlays.base.qml_bridge import QmlBridge

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdPageBase(QmlBridge):
    """Hostable page content: business logic plus a diff-cached bridge to the
    active page QML item. Pages own no window and no transport — they receive
    events exclusively from their host (MfdOverlay or StandalonePageHost)
    calling dispatch_event.

    Concrete pages subclass this and define KEY, PAGE_QML_FILE, OVERLAY_ID.
    Per-page config is plain typed __init__ args, set before calling
    super().__init__ (which runs setup_page).
    """

    KEY: str = ""
    PAGE_QML_FILE: Path = ""
    OVERLAY_ID: str = ""  # window identity used when hosted by StandalonePageHost

    def __init__(self, logger: logging.Logger):
        assert self.KEY, "KEY must be set in subclass"
        assert self.PAGE_QML_FILE, "PAGE_QML_FILE must be set in subclass"
        assert Path(self.PAGE_QML_FILE).exists(), f"PAGE_QML_FILE does not exist: {self.PAGE_QML_FILE}"

        QmlBridge.__init__(self)
        self._page_item = None
        self.logger = logger

        self.setup_page()

    # ------------------------------------------------------------------
    # QmlBridge: qml_target implementation
    # ------------------------------------------------------------------
    @property
    def qml_target(self):
        return self._page_item

    # ------------------------------------------------------------------
    # Abstract hook
    # ------------------------------------------------------------------
    def setup_page(self) -> None:
        """Initialise page state and register event handlers. Must be overridden in subclasses.

        Called at the end of __init__ — subclasses must set their config fields
        before calling super().__init__.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Page lifecycle
    # ------------------------------------------------------------------
    def _on_page_activated(self, item: QQuickItem):
        """Internal activation — stores item, clears prop cache, then calls the public hook."""
        self._page_item = item
        self._on_target_changed()  # clears _props cache for the fresh item
        self._stats.track_event("__LIFECYCLE__", "activated")
        self.logger.debug("%s | Page activated", self.KEY)
        self.on_page_activated()

    def on_page_activated(self):
        """Called when the page becomes active. Override in subclasses with @final."""

    def on_page_deactivated(self):
        """Called when the page is deactivated."""
        self._page_item = None
        self._stats.track_event("__LIFECYCLE__", "deactivated")
        self.logger.debug("%s | Page deactivated", self.KEY)

    @property
    def is_active(self) -> bool:
        return self._page_item is not None
