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

import math
from dataclasses import dataclass
from typing import ClassVar

from .base import Stat

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------


@dataclass(slots=True)
class FrameRenderStat(Stat):
    """Frame render-time distribution tracker for high-frequency overlays.

    Tracks:
        - `count`: number of rendered frames observed.
        - `min` / `max`: extrema of observed frame durations.
        - `avg` / `variance`: running population statistics of frame durations.
        - `stddev`: running population standard deviation of frame durations.
        - `missed_budget`: number of frames exceeding `frame_budget_ns`.
        - `frame_budget_ns`: configured per-frame render budget.
    """

    TYPE: ClassVar[str] = "__FRAME_RENDER__"

    min: int = 2**63 - 1
    max: int = 0
    mean: float = 0.0
    m2: float = 0.0

    missed_budget: int = 0
    frame_budget_ns: int = 0

    def observe_frame(self, duration_ns: int) -> None:
        """Observe one frame duration sample and update running stats."""
        self.count += 1

        self.min = min(self.min, duration_ns)
        self.max = max(self.max, duration_ns)

        if duration_ns > self.frame_budget_ns:
            self.missed_budget += 1

        # Welford running mean/variance
        delta = duration_ns - self.mean
        self.mean += delta / self.count
        delta2 = duration_ns - self.mean
        self.m2 += delta * delta2

    def variance(self) -> float:
        """Return population variance of observed frame durations."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    def stddev(self) -> float:
        """Return population standard deviation of observed frame durations."""
        return math.sqrt(self.variance())

    def to_dict(self) -> dict:
        """Serialize this frame-render stat to a JSON-friendly dictionary."""
        min_val = self.min if self.count > 0 else 0
        max_val = self.max if self.count > 0 else 0

        return {
            "type": self.TYPE,
            "count": self.count,
            "min_ns": min_val,
            "max_ns": max_val,
            "avg_ns": self.mean,
            "variance_ns": self.variance(),
            "stddev_ns": self.stddev(),
            "missed_budget": self.missed_budget,
        }
