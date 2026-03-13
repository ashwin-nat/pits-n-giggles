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

from collections import defaultdict
from typing import Dict, Optional

import time

from .base import Stat
from .frame_render import FrameTimingStat
from .latency import LatencyStat
from .packet import PacketStat

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------


class EventCounter:
    """
    Generic hierarchical stats tracker.

    Structure:
        category -> subcategory -> Stat

    Caller is responsible for using the correct API:
        - track_event()
        - track_packet()
        - track_packet_latency()
        - track_frame_render()
    """

    def __init__(self) -> None:
        """Initialize an empty hierarchical stats store."""
        # Only outer level uses defaultdict
        self._stats: Dict[str, Dict[str, Stat]] = defaultdict(dict)

    # --------------------------------------------------
    # Tracking APIs
    # --------------------------------------------------

    def track_event(self, category: str, subcategory: str) -> None:
        """Record a generic count-only event under `category/subcategory`."""
        bucket = self._stats[category]

        stat = bucket.get(subcategory)
        if stat is None:
            stat = Stat()
            bucket[subcategory] = stat

        stat.increment()

    def track_packet(self, category: str, subcategory: str, size: int) -> None:
        """Record a packet event and accumulate its payload size in bytes."""
        bucket = self._stats[category]

        stat = bucket.get(subcategory)
        if stat is None:
            stat = PacketStat()
            bucket[subcategory] = stat

        stat.increment_with_size(size)

    def track_packet_latency(self, category: str, subcategory: str, send_ts_ns: int,
                             recv_ts_ns: Optional[int] = None) -> None:
        """Record a packet latency sample under `category/subcategory`.

        Args:
            category: Top-level group name (for example, `udp`).
            subcategory: Nested stat name (for example, `ingest`).
            send_ts_ns: Sender timestamp in nanoseconds.
            recv_ts_ns: Receiver timestamp in nanoseconds (Optional).
        """
        if recv_ts_ns is None:
            recv_ts_ns = time.time_ns()

        bucket = self._stats[category]

        stat = bucket.get(subcategory)
        if stat is None:
            stat = LatencyStat()
            bucket[subcategory] = stat

        stat.observe_packet(send_ts_ns, recv_ts_ns)

    def track_frame_render(self, category: str, subcategory: str, duration_ns: int,
                           fps: int) -> None:
        """Record a frame render duration sample under `category/subcategory`.

        Args:
            category: Top-level group name (for example, `qml_overlay`).
            subcategory: Nested stat name (for example, `hud`).
            duration_ns: Frame render time in nanoseconds.
            fps: Target frames per second used to derive frame budget.
        """
        bucket = self._stats[category]

        stat = bucket.get(subcategory)
        if stat is None:
            stat = FrameTimingStat(frame_budget_ns=1_000_000_000 // fps)
            bucket[subcategory] = stat

        stat.observe_frame(duration_ns)

    # --------------------------------------------------
    # Access
    # --------------------------------------------------

    def get_stats(self) -> dict:
        """Return a serialized snapshot of all tracked stats."""
        return {
            category: {
                subcategory: stat.to_dict()
                for subcategory, stat in bucket.items()
            }
            for category, bucket in self._stats.items()
        }
