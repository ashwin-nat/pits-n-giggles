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
class Stat:
    count: int = 0
    bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "bytes": self.bytes,
        }

class EventCounter:
    """
    Generic hierarchical stats tracker.

    Structure:
        category -> subcategory -> Stat

    Example:
        tracker.track("udp", "raw", 1200)
        tracker.track("udp", "parsed", 800)
        tracker.track("zmq", "forwarded", 1024)
    """

    def __init__(self) -> None:
        self._stats: Dict[str, Dict[str, Stat]] = defaultdict(
            lambda: defaultdict(Stat)
        )

    # --------------------------------------------------
    # Tracking
    # --------------------------------------------------

    def track(
        self,
        category: str,
        subcategory: str,
        size: int,
    ) -> None:
        stat = self._stats[category][subcategory]
        stat.count += 1
        stat.bytes += size

    # --------------------------------------------------
    # Access
    # --------------------------------------------------

    def get_stats(self) -> dict:
        return {
            category: {
                subcategory: stat.to_dict()
                for subcategory, stat in bucket.items()
            }
            for category, bucket in self._stats.items()
        }

