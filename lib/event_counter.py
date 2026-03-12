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
from dataclasses import dataclass
from typing import Dict, ClassVar, Optional

import math
import time

# -------------------------------------- FUNCTIONS --------------------------------------------------------------------

@dataclass(slots=True)
class Stat:
    """Generic simple event counter for non-payload events.

    Tracks:
        - `count`: number of occurrences of an event.
    """

    TYPE: ClassVar[str] = "__COUNT__"
    count: int = 0

    def increment(self) -> None:
        """Increase the event count by one."""
        self.count += 1

    def to_dict(self) -> dict:
        """Serialize this stat to a JSON-friendly dictionary."""
        return {
            "type": self.TYPE,
            "count": self.count,
        }


@dataclass(slots=True)
class PacketStat(Stat):
    """Packet throughput counter with cumulative payload size.

    Tracks:
        - `count`: number of packets observed.
        - `bytes`: total payload bytes across observed packets.
    """

    TYPE: ClassVar[str] = "__PACKET__"
    bytes: int = 0

    def increment_with_size(self, size: int) -> None:
        """Record one packet and add its payload size to total bytes."""
        self.count += 1
        self.bytes += size

    def to_dict(self) -> dict:
        """Serialize this packet stat to a JSON-friendly dictionary."""
        return {
            "type": self.TYPE,
            "count": self.count,
            "bytes": self.bytes,
        }

@dataclass(slots=True)
class LatencyStat(Stat):
    """Latency distribution tracker for packet timing.

    Tracks:
        - `count`: number of valid latency samples used in the model.
        - `bad_latency_count`: number of invalid samples (negative latency).
        - `min` / `max`: extrema of valid latencies.
        - `avg` / `variance`: running population statistics of valid latencies.
        - `stddev`: running population standard deviation of valid latencies.
    """

    TYPE: ClassVar[str] = "__LATENCY__"

    min: int = 2**63 - 1
    max: int = 0
    bad_latency_count: int = 0

    mean: float = 0.0
    m2: float = 0.0

    def observe_packet(self, sender_ts_ns: int, recv_ts_ns: int) -> None:
        """Observe one packet timing sample and update running latency stats.

        Negative latency samples are counted as bad data and ignored.
        """
        latency = recv_ts_ns - sender_ts_ns

        # Guard against rare clock adjustments: track bad samples but
        # do not let them influence min/max/mean/variance.
        if latency < 0:
            self.bad_latency_count += 1
            return

        self.count += 1

        if latency < self.min:
            self.min = latency
        if latency > self.max:
            self.max = latency

        # Welford running mean/variance
        delta = latency - self.mean
        self.mean += delta / self.count
        delta2 = latency - self.mean
        self.m2 += delta * delta2

    def variance(self) -> float:
        """Return population variance of valid latency samples."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    def stddev(self) -> float:
        """Return population standard deviation of valid latency samples."""
        return math.sqrt(self.variance())

    def to_dict(self) -> dict:
        """Serialize this latency stat to a JSON-friendly dictionary."""
        min_val = self.min if self.count > 0 else 0
        max_val = self.max if self.count > 0 else 0

        return {
            "type": self.TYPE,
            "count": self.count,
            "bad_latency_count": self.bad_latency_count,
            "min_ns": min_val,
            "max_ns": max_val,
            "avg_ns": self.mean,
            "variance_ns": self.variance(),
            "stddev_ns": self.stddev(),
        }

class EventCounter:
    """
    Generic hierarchical stats tracker.

    Structure:
        category -> subcategory -> Stat

    Caller is responsible for using the correct API:
        - track_event()
        - track_packet()
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
