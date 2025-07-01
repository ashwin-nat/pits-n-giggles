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

from enum import Enum, auto
from typing import Any, Callable, Set, Dict

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class DriverPendingEvents(Enum):
    """
    Enum class representing possible pending events for a driver.
    """
    LAP_CHANGE_EVENT = auto()
    CAR_DMG_PKT_EVENT = auto()

    def __repr__(self) -> str:
        """
        Returns the name of the enum member as a string.

        Returns:
            str: Name of the enum member.
        """
        return self.name

    def __str__(self) -> str:
        """
        Returns the name of the enum member as a string.

        Returns:
            str: Name of the enum member.
        """
        return self.name

class PendingEventsManager:
    """
    Manages a set of pending events. When all registered events have occurred at least once,
    the callback is triggered with optional keyword arguments provided during registration.
    """

    def __init__(self, callback: Callable[..., None]):
        """
        Initializes the PendingEventsManager.

        Args:
            callback (Callable[..., None]): Function to call once all registered events have occurred.
                                            Can accept keyword arguments.
        """
        self._pending_events: Set[DriverPendingEvents] = set()
        self._callback: Callable[..., None] = callback
        self._callback_kwargs: Dict[str, Any] = {}
        self._opt_data: Any = None

    def register(self,
                 events: Set[DriverPendingEvents],
                 **kwargs: Any) -> None:
        """
        Registers the set of events to wait for and optional keyword arguments for the callback.

        Args:
            events (Set[DriverPendingEvents]): Events that must occur before the callback is triggered.
            **kwargs (Any): Keyword arguments to pass to the callback.
        """
        self._pending_events = set(events)
        self._callback_kwargs = kwargs

    def onEvent(self, event: DriverPendingEvents) -> None:
        """
        Called when an event occurs. If the event is one of the registered pending events,
        it is removed. If all pending events have occurred, the callback is triggered
        with the previously registered keyword arguments.

        Args:
            event (DriverPendingEvents): The event that occurred.
        """
        if event not in self._pending_events:
            return

        self._pending_events.remove(event)
        if not self._pending_events:
            self._callback(**self._callback_kwargs)
            self._opt_data = None

    def areEventsPending(self) -> bool:
        """
        Returns whether there are any pending events.

        Returns:
            bool: True if there are pending events, False otherwise.
        """
        return bool(self._pending_events)

    @property
    def data(self) -> Any:
        """Getter for the optional data."""
        return self._opt_data

    @data.setter
    def data(self, data: Any):
        """Setter for the optional data. The optional data will be cleared after the callback is triggered."""
        self._opt_data = data
