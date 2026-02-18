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

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from lib.f1_types import F1PacketType

# -------------------------------------- FUNCTIONS --------------------------------------------------------------------

@dataclass(slots=True)
class PacketStat:
    count: int = 0
    bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "bytes": self.bytes,
        }


class PacketStatsTracker:
    """
    Tracks packet statistics using a single stats dataclass.

    - Global stats stored as PacketStat
    - Per-packet-type stats stored in dict[str, PacketStat]
    - Start time at ctor
    - Injectable clock for testing
    """

    def __init__(
        self,
        start_time: Optional[float] = None,
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self._time_fn = time_fn
        self._start_time = start_time if start_time is not None else self._time_fn()

        # Global stats
        self._parsed_global = PacketStat()
        self._raw_global = PacketStat()

        # packet_name -> PacketStat
        self._per_type: Dict[str, PacketStat] = defaultdict(PacketStat)

        # category -> (packet_name -> PacketStat)
        self._categories: Dict[str, Dict[str, PacketStat]] = defaultdict(
            lambda: defaultdict(PacketStat)
        )

        # PPS tracking
        self._last_pps_check_time = self._start_time
        self._last_pps_packet_count = 0
        self._instant_pps: float = 0.0

    # --------------------------------------------------
    # Tracking
    # --------------------------------------------------

    def track_raw(self, pkt_len: int) -> None:
        self._raw_global.count += 1
        self._raw_global.bytes += pkt_len

    def track_parsed(
        self,
        packet_type: F1PacketType,
        packet_size: int,
    ) -> None:
        # Update global
        self._parsed_global.count += 1
        self._parsed_global.bytes += packet_size

        # Update per-type
        stat = self._per_type[pkt_name]
        pkt_name = str(packet_type)
        stat.count += 1
        stat.bytes += packet_size

    def track_custom(
        self,
        category: str,
        packet_type: F1PacketType,
        packet_size: int,
    ) -> None:
        pkt_name = str(packet_type)

        stat = self._categories[category][pkt_name]
        stat.count += 1
        stat.bytes += packet_size

    def track_custom_raw(
        self,
        category: str,
        packet_name: str,
        packet_size: int,
    ) -> None:
        stat = self._categories[category][packet_name]
        stat.count += 1
        stat.bytes += packet_size

    # --------------------------------------------------
    # Stats
    # --------------------------------------------------

    def get_stats(self) -> dict:
        self._update_pps()

        runtime = self._time_fn() - self._start_time
        avg_pps = (
            self._parsed_global.count / runtime
            if runtime > 0
            else 0.0
        )

        return {
            "runtime-seconds": runtime,
            "parsed": self._parsed_global.to_dict(),
            "raw": self._raw_global.to_dict(),
            "average-pps": avg_pps,
            "instant-pps": self._instant_pps,
            "per-type": {
                name: stat.to_dict()
                for name, stat in self._per_type.items()
            },
            "categories": {
                category: {
                    name: stat.to_dict()
                    for name, stat in bucket.items()
                }
                for category, bucket in self._categories.items()
            },
        }

    def reset(self) -> None:
        self.__init__(time_fn=self._time_fn)

    # --------------------------------------------------
    # PPS
    # --------------------------------------------------

    def _update_pps(self) -> None:
        now = self._time_fn()
        elapsed = now - self._last_pps_check_time

        if elapsed >= 1.0:
            delta = (
                self._parsed_global.count
                - self._last_pps_packet_count
            )

            self._instant_pps = (
                delta / elapsed if elapsed > 0 else 0.0
            )

            self._last_pps_packet_count = (
                self._parsed_global.count
            )
            self._last_pps_check_time = now
