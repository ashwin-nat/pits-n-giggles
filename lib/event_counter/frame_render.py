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
class FrameTimingStat(Stat):
    """Frame interval and FPS tracker with pacing diagnostics.

    Tracks:
        - `count`: number of valid frame intervals observed.
        - `min` / `max`: extrema of observed frame intervals.
        - `mean` / `variance`: running population statistics of intervals.
        - `stddev`: running population standard deviation of intervals.
        - `missed_frames`: intervals that exceed configured frame budget.
        - `max_miss_streak`: longest consecutive miss streak observed.
        - `pacing_error_sum` / `max_pacing_error`: absolute deviation from budget.
    """

    TYPE: ClassVar[str] = "__FRAME_TIMING__"

    min: int = 2**63 - 1
    max: int = 0
    mean: float = 0.0
    m2: float = 0.0

    frame_budget_ns: int = 0

    missed_frames: int = 0
    current_miss_streak: int = 0
    max_miss_streak: int = 0

    pacing_error_sum: int = 0
    max_pacing_error: int = 0

    last_ts_ns: int = 0

    def observe_frame(self, now_ns: int) -> None:
        """Observe one frame timestamp and update timing diagnostics.

        Args:
            now_ns: Current frame timestamp in nanoseconds.
        """

        if self.last_ts_ns == 0:
            self.last_ts_ns = now_ns
            return

        interval = now_ns - self.last_ts_ns
        self.last_ts_ns = now_ns

        if interval <= 0:
            return

        self.count += 1

        if interval < self.min:
            self.min = interval

        if interval > self.max:
            self.max = interval

        # Welford running variance
        delta = interval - self.mean
        self.mean += delta / self.count
        delta2 = interval - self.mean
        self.m2 += delta * delta2

        # budget tracking
        if self.frame_budget_ns:
            if interval > self.frame_budget_ns:
                self.missed_frames += 1
                self.current_miss_streak += 1

                if self.current_miss_streak > self.max_miss_streak:
                    self.max_miss_streak = self.current_miss_streak
            else:
                self.current_miss_streak = 0

            # pacing error
            error = interval - self.frame_budget_ns
            abs_error = abs(error)

            self.pacing_error_sum += abs_error

            if abs_error > self.max_pacing_error:
                self.max_pacing_error = abs_error

    def variance(self) -> float:
        """Return population variance of observed frame intervals."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    def stddev(self) -> float:
        """Return population standard deviation of frame intervals."""
        return math.sqrt(self.variance())

    def to_dict(self) -> dict:
        """Serialize this frame timing stat to a JSON-friendly dictionary."""

        if self.count == 0:
            min_val = 0
            max_val = 0
        else:
            min_val = self.min
            max_val = self.max

        avg_fps = 0.0
        min_fps = 0.0
        max_fps = 0.0
        target_fps = 0.0
        miss_ratio = 0.0
        avg_pacing_error = 0.0

        if self.mean > 0:
            avg_fps = 1e9 / self.mean

        if max_val > 0:
            min_fps = 1e9 / max_val

        if min_val > 0:
            max_fps = 1e9 / min_val

        if self.frame_budget_ns > 0:
            target_fps = 1e9 / self.frame_budget_ns

        if self.count > 0:
            miss_ratio = self.missed_frames / self.count
            avg_pacing_error = self.pacing_error_sum / self.count

        return {
            "type": self.TYPE,
            "count": self.count,

            "interval_ns": {
                "avg": self.mean,
                "stddev": self.stddev(),
                "variance": self.variance(),
                "min": min_val,
                "max": max_val,
            },

            "fps": {
                "avg": avg_fps,
                "min": min_fps,
                "max": max_fps,
                "target": target_fps,
            },

            "budget": {
                "missed_frames": self.missed_frames,
                "miss_ratio": miss_ratio,
                "max_miss_streak": self.max_miss_streak,
            },

            "pacing_error_ns": {
                "avg": avg_pacing_error,
                "max": self.max_pacing_error,
            },
        }
