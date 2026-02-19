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
from typing import TYPE_CHECKING, Any, Callable, Dict

from PySide6.QtQuick import QQuickItem

from lib.event_counter import EventCounter

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd import MfdOverlay

# -------------------------------------- TYPES -------------------------------------------------------------------------

EventCommandHandler = Callable[[Dict[str, Any]], None] # Takes dict arg, returns None

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdPageBase:
    KEY: str = ""
    QML_FILE: Path = ""

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        assert self.KEY, "KEY must be set in subclass"
        assert self.QML_FILE, "Derived classes must define QML_FILE"
        assert isinstance(self.QML_FILE, Path), "QML_FILE must be a pathlib.Path"
        assert self.QML_FILE.is_file(), f"QML_FILE does not exist or is not a file: {self.QML_FILE}"

        self.overlay = overlay
        self._page_item = None
        self.logger = logger
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._stats = EventCounter()

    def on_event(self, event_type: str):
        """Decorator to register an event handler for this page."""
        def decorator(fn):
            self._handlers[event_type] = fn
            return fn
        return decorator

    def get_handled_event_types(self) -> set:
        """Return the set of event types this page handles."""
        return set(self._handlers.keys())

    def handles_event(self, event_type: str) -> bool:
        """Check if this page handles a specific event type."""
        return event_type in self._handlers

    def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle an event if this page has a handler registered for it."""
        if handler := self._handlers.get(event_type):
            self._track_event(event_type)
            try:
                handler(data)
            except Exception: # pylint: disable=broad-exception-caught
                self._stats.track("__EXCEPTION__", event_type, 0)
                raise

    def get_stats(self) -> dict:
        """Get page runtime stats."""
        return self._stats.get_stats()

    def _track_event(self, event_type: str) -> None:
        self._stats.track("__EVENTS__", "__TOTAL__", 0)
        self._stats.track("__EVENTS__", event_type, 0)

    @property
    def root(self):
        return self.overlay._root

    @property
    def page_item(self):
        return self.overlay.current_page_item

    def on_page_activated(self, item: QQuickItem):
        """Called when the page becomes active. Interested overlays should override this method."""
        self._page_item = item
        self._stats.track("__LIFECYCLE__", "activated", 0)
        self.logger.debug(f"{self.KEY} | Page activated")

    def on_page_deactivated(self):
        """Called when the page becomes active. Interested overlays should override this method."""
        self._page_item = None
        self._stats.track("__LIFECYCLE__", "deactivated", 0)
        self.logger.debug(f"{self.KEY} | Page deactivated")

    @property
    def is_active(self) -> bool:
        return self._page_item is not None
