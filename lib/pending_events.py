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
from typing import Callable, List

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class PendingEventType(Enum):
    """
    Base enum class for event types.
    All specific event type enums should derive from this class.
    """

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

class DriverPendingEvents(PendingEventType):
    """
    Enum class representing possible pending events for a driver.
    """
    LAP_CHANGE_EVENT = auto()
    CAR_DMG_PKT_EVENT = auto()

class PendingEventsManager:
    """
    Manages a set of pending events. When all registered events have occurred at least once,
    the callback is triggered with optional keyword arguments provided during registration.
    """

    def __init__(self, callback: Callable[..., None], in_order: bool = False):
        """
        Initializes the PendingEventsManager.

        Args:
            callback (Callable[..., None]): Function to call once all registered events have occurred.
                                            Can accept keyword arguments.
            in_order (bool): If True, events must occur in the order they were registered.
                           If False, events can occur in any order. Defaults to False.
        """
        self._pending_events: List[PendingEventType] = []
        self._callback: Callable[..., None] = callback
        self._in_order: bool = in_order

    def register(self,
                 events: List[PendingEventType]) -> None:
        """
        Registers the set of events to wait for and optional keyword arguments for the callback.

        Args:
            events (List[PendingEventType]): Events that must occur before the callback is triggered.
        """
        self._pending_events = events

    def onEvent(self, event: PendingEventType) -> None:
        """
        Called when an event occurs. If the event is one of the registered pending events,
        it is removed. If all pending events have occurred, the callback is triggered
        with the previously registered keyword arguments.

        Args:
            event (PendingEventType): The event that occurred.
        """
        if self._in_order:
            # In order mode: only process if it's the first pending event
            if self._pending_events and self._pending_events[0] == event:
                del self._pending_events[0]
        else:
            # Any order mode: remove the event if it exists anywhere in the list
            idx = next(
                (i for i, e in enumerate(self._pending_events) if e == event),
                None,
            )

            if idx is None:
                return

            del self._pending_events[idx]

        if not self._pending_events:
            self._callback()

    def areEventsPending(self) -> bool:
        """
        Returns whether there are any pending events.

        Returns:
            bool: True if there are pending events, False otherwise.
        """
        return bool(self._pending_events)
