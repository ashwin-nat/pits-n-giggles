# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from typing import Generic, Optional, Tuple, TypeVar

from lib.event_counter import EventCounter

# -------------------------------------- TYPES -------------------------------------------------------------------------

T = TypeVar("T")

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LatestSlot(Generic[T]):
    """Single-writer, multi-reader latest-value slot with built-in publish/coalesce stats.

    publish() bundles the payload with a freshly assigned seq into a single
    (payload, seq) tuple and stores it with a single reference swap; take()
    reads that reference once. No lock is needed: under the GIL a single
    reference assignment/read is atomic, so a reader never observes a
    payload paired with the wrong seq. Callers on the write side must
    finish building/mutating the payload before calling publish() and never
    touch it afterwards.

    Stats are recorded into a caller-supplied, shared EventCounter under
    `name`, so a caller with several slots (e.g. one per topic) gets them all
    in one flat stats store instead of merging per-slot counters by hand.
    Consumers get this for free too: take_if_new() records a message as
    coalesced whenever it is skipped, so callers never need their own
    dropped/skipped bookkeeping.
    """

    def __init__(self, name: str, stats: EventCounter) -> None:
        self._name = name
        self._stats = stats
        self._snapshot: Optional[Tuple[T, int]] = None
        self._next_seq: int = 0

    def publish(self, payload: T) -> int:
        """Store payload as the latest value. Returns the seq assigned to it."""
        self._next_seq += 1
        seq = self._next_seq
        self._snapshot = (payload, seq)
        self._stats.track_event(self._name, "__MAILBOX_PUBLISHED__")
        return seq

    def take(self) -> Optional[Tuple[T, int]]:
        """Read the current value once, unconditionally. Returns None if nothing
        has been published yet."""
        return self._snapshot

    def take_if_new(self, last_seq: int) -> Optional[Tuple[T, int]]:
        """Read the current value only if it is newer than last_seq (the caller's
        own last-processed seq for this slot).

        Returns None when the value is unchanged or nothing has been
        published yet — and records the skip as coalesced — so a caller
        driven by repeated notifications (e.g. one doorbell per publish) can
        collapse a backlog to O(1) skips without tracking drops itself.
        """
        snapshot = self._snapshot
        if snapshot is None:
            return None
        if snapshot[1] == last_seq:
            self._stats.track_event(self._name, "__MAILBOX_COALESCED__")
            return None
        return snapshot
