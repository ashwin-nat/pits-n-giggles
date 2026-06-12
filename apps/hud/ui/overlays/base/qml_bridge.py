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

from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QObject

from lib.event_counter import EventCounter

# -------------------------------------- TYPES -------------------------------------------------------------------------

_UNSET = object()  # sentinel for absent property cache entries

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class QmlBridge:
    """Conceptually pure-Python base shared by BaseOverlay and MfdPageBase;
    it only references QObject for typing convenience.

    Provides three things:
    - Stats: single EventCounter per component; get_stats(), _track_event().
    - Diff-based QML property caching: set_qml_property(), invalidate_qml_cache(),
      _on_target_changed() (clears cache).
    - Event handler registry: on_event() decorator (always guarded on
      _qml_target is not None), dispatch_event(), get_handled_event_types(),
      handles_event().

    Subclasses must implement the _qml_target property, which returns the live
    QObject to write properties to (QQuickWindow for overlays, QQuickItem
    for pages).  Returning None signals that the target is not yet ready.
    External callers must use set_qml_property() and dispatch_event() rather
    than accessing _qml_target directly.
    """

    def __init__(self):
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._stats = EventCounter()
        self._props: dict = {}

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------
    @property
    def _qml_target(self) -> Optional[QObject]:
        """Return the live QObject target, or None if not yet ready."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Property cache
    # ------------------------------------------------------------------
    def _on_target_changed(self) -> None:
        """Call when qml_target changes to a new object; clears the prop cache."""
        self._props.clear()

    def set_qml_property(self, name: str, value) -> None:
        """Write a property to qml_target with diff-based caching.

        Silently does nothing when qml_target is None or the value is unchanged.
        """
        target = self._qml_target
        if target is None:
            self._stats.track_event("__PROPS_NO_TARGET__", name)
            return
        if self._props.get(name, _UNSET) == value:
            self._stats.track_event("__PROPS_CACHED__", name)
            return
        self._props[name] = value
        target.setProperty(name, value)
        self._stats.track_event("__PROPS__", name)

    def invalidate_qml_cache(self, *names: str) -> None:
        """Remove entries from the prop cache so next set_qml_property always pushes."""
        for name in names:
            self._props.pop(name, None)

    # ------------------------------------------------------------------
    # Event handler registry
    # ------------------------------------------------------------------
    def on_event(self, event_type: str):
        """Decorator to register a handler for event_type.

        The registered wrapper skips the handler (counting __DROPPED_NO_TARGET__)
        when qml_target is None.  The requires_root / requires_page_item
        parameter from the old API is removed — the guard is always wanted.
        """
        def decorator(fn):
            def wrapper(data, _n=event_type):
                if self._qml_target is None:
                    self._stats.track_event("__DROPPED_NO_TARGET__", _n)
                    return None
                return fn(data)
            self._handlers[event_type] = wrapper
            return fn
        return decorator

    def dispatch_event(self, name: str, data: dict) -> None:
        """Dispatch name to the registered handler, if any.

        Tracks __EVENTS__ on delivery and __EXCEPTION__ on error (re-raises).
        """
        handler = self._handlers.get(name)
        if handler is None:
            return
        self._track_event(name)
        try:
            handler(data)
        except Exception:
            self._stats.track_event("__EXCEPTION__", name)
            raise

    def get_handled_event_types(self) -> set:
        """Return the set of event types this component handles."""
        return set(self._handlers.keys())

    def handles_event(self, event_type: str) -> bool:
        """True if a handler is registered for event_type."""
        return event_type in self._handlers

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return runtime stats from this component's EventCounter."""
        return self._stats.get_stats()

    def _track_event(self, event_type: str) -> None:
        self._stats.track_event("__EVENTS__", "__TOTAL__")
        self._stats.track_event("__EVENTS__", event_type)
