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
from typing import Any, Callable, Dict

from PySide6.QtQuick import QQuickItem

from lib.event_counter import EventCounter

# -------------------------------------- TYPES -------------------------------------------------------------------------

EventCommandHandler = Callable[[Dict[str, Any]], None] # Takes dict arg, returns None

_UNSET = object()  # sentinel for absent page-property cache entries

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdPageBase:
    """Hostable page content: business logic plus a diff-cached bridge to the
    active page QML item. Pages own no window and no transport — they receive
    events exclusively from their host (MfdOverlay or StandalonePageHost)
    calling handle_event.

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

        self._page_item = None
        self.logger = logger
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._stats = EventCounter()
        self._page_props: dict = {}

        self.setup_page()

    def setup_page(self) -> None:
        """Initialise page state and register event handlers. Must be overridden in subclasses.

        Called at the end of __init__ — subclasses must set their config fields
        before calling super().__init__.
        """
        raise NotImplementedError

    def on_event(self, event_type: str, requires_root: bool = True):
        """Decorator to register an event handler for this page.

        Mirrors the BaseOverlay.on_event signature so page code is identical
        to overlay code. Here "root" means the active page QML item.

        Args:
            event_type: The event type to handle.
            requires_root: If True (default), the handler is skipped when the page is not active.
        """
        def decorator(fn):
            if requires_root:
                def wrapper(data, _event_type=event_type):
                    if not self._page_item:
                        self._stats.track_event("__DROPPED_NO_PAGE__", _event_type)
                        return None
                    return fn(data)
                self._handlers[event_type] = wrapper
            else:
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
            except Exception:
                self._stats.track_event("__EXCEPTION__", event_type)
                raise

    def get_stats(self) -> dict:
        """Get page runtime stats."""
        return self._stats.get_stats()

    def _track_event(self, event_type: str) -> None:
        self._stats.track_event("__EVENTS__", "__TOTAL__")
        self._stats.track_event("__EVENTS__", event_type)

    def set_qml_property(self, name: str, value) -> None:
        """Set a property on the active page QML item with diff-based caching.

        Silently does nothing when the page is not active or the value is
        unchanged since the last push.
        """
        if self._page_item is None:
            self._stats.track_event("__PROPS_NO_PAGE__", name)
            return
        if self._page_props.get(name, _UNSET) == value:
            self._stats.track_event("__PROPS_CACHED__", name)
            return
        self._page_props[name] = value
        self._page_item.setProperty(name, value)
        self._stats.track_event("__PROPS__", name)

    def _on_page_activated(self, item: QQuickItem):
        """Internal activation — stores item, tracks stats, then calls the public hook."""
        self._page_item = item
        self._page_props.clear()  # fresh item — invalidate all cached property values
        self._stats.track_event("__LIFECYCLE__", "activated")
        self.logger.debug("%s | Page activated", self.KEY)
        self.on_page_activated()

    def on_page_activated(self):
        """Called when the page becomes active. Override in subclasses with @final."""

    def on_page_deactivated(self):
        """Called when the page becomes active. Interested overlays should override this method."""
        self._page_item = None
        self._stats.track_event("__LIFECYCLE__", "deactivated")
        self.logger.debug("%s | Page deactivated", self.KEY)

    @property
    def is_active(self) -> bool:
        return self._page_item is not None
