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
from collections import deque
from dataclasses import dataclass, field
from typing import ClassVar

from .base import Stat

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_WINDOW_SIZE: int = 512

# An active interval longer than this multiple of the display period is a hitch:
# a frame the viewer perceived as a stutter. Missing vsync by a few percent is
# not perceptible; skipping a whole frame is.
_HITCH_FACTOR: float = 2.0

# A gap longer than max(_BOUNDARY_FACTOR x period, _MIN_BOUNDARY_NS) is an idle
# boundary, not a slow frame: the window simply had nothing to draw.
_BOUNDARY_FACTOR: int = 3
_MIN_BOUNDARY_NS: int = 100_000_000  # 100 ms

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------


@dataclass(slots=True)
class PresentSmoothnessStat(Stat):
    """Rendering smoothness tracker for on-demand presented frames.

    Presented frames carry no rate contract - a window renders only when its
    content changes - so raw intervals are only meaningful inside an "active
    burst" of continuous rendering. A gap longer than the idle boundary
    resets the baseline and records nothing: idle time is on-demand rendering
    working, not jank. Within a burst, an interval longer than
    _HITCH_FACTOR x display period counts as a hitch.

    The display period is supplied per observation so a window that migrates
    between monitors with different refresh rates stays correctly calibrated.

    Tracks:
        - `count`: active (intra-burst) intervals observed.
        - `presents`: total presents observed (including burst starts).
        - `boundaries`: idle boundaries (burst starts after a gap).
        - `hitches`: active intervals exceeding the hitch threshold.
        - `bad_samples`: non-positive intervals or invalid display periods.
        - `active_time_ns`: sum of active intervals.
        - `min` / `max` / `mean` / `variance`: over active intervals.
        - `p50` / `p95` / `p99`: over a rolling window of active intervals.
    """

    TYPE: ClassVar[str] = "__PRESENT_SMOOTHNESS__"

    presents: int = 0
    boundaries: int = 0
    hitches: int = 0
    bad_samples: int = 0

    active_time_ns: int = 0

    min: int = 2**63 - 1
    max: int = 0
    mean: float = 0.0
    m2: float = 0.0

    # Rolling window for percentile computation (O(1) append, sorted at read time).
    samples: deque = field(default_factory=lambda: deque(maxlen=_WINDOW_SIZE))

    last_ts_ns: int = 0

    def observe_present(self, now_ns: int, period_ns: int) -> None:
        """Observe one presented-frame timestamp.

        Args:
            now_ns: Presentation timestamp in nanoseconds (captured at emission).
            period_ns: Display period of the window's current screen in nanoseconds.
        """
        if period_ns <= 0:
            self.bad_samples += 1
            return

        self.presents += 1

        if self.last_ts_ns == 0:
            self.last_ts_ns = now_ns
            return

        interval = now_ns - self.last_ts_ns
        self.last_ts_ns = now_ns

        if interval <= 0:
            self.bad_samples += 1
            return

        if interval > max(_BOUNDARY_FACTOR * period_ns, _MIN_BOUNDARY_NS):
            self.boundaries += 1
            return

        self.count += 1
        self.active_time_ns += interval

        self.min = min(self.min, interval)
        self.max = max(self.max, interval)

        # Welford running mean/variance
        delta = interval - self.mean
        self.mean += delta / self.count
        delta2 = interval - self.mean
        self.m2 += delta * delta2

        self.samples.append(interval)

        if interval > _HITCH_FACTOR * period_ns:
            self.hitches += 1

    def variance(self) -> float:
        """Return population variance of active intervals."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    def stddev(self) -> float:
        """Return population standard deviation of active intervals."""
        return math.sqrt(self.variance())

    def to_dict(self) -> dict:
        """Serialize this stat to a JSON-friendly dictionary.

        Percentile computation (sort) happens here, not in the hot path.
        """
        min_val = self.min if self.count > 0 else 0
        max_val = self.max if self.count > 0 else 0

        n = len(self.samples)
        if n > 0:
            sorted_samples = sorted(self.samples)
            p50 = sorted_samples[int((n - 1) * 0.50)]
            p95 = sorted_samples[int((n - 1) * 0.95)]
            p99 = sorted_samples[int((n - 1) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        active_time_s = self.active_time_ns / 1e9
        hitch_ratio = (self.hitches / self.count) if self.count > 0 else 0.0
        hitches_per_active_min = (self.hitches / (active_time_s / 60.0)) if active_time_s > 0 else 0.0

        return {
            "type": self.TYPE,
            "count": self.count,
            "presents": self.presents, # Every present observed, including burst starts
            "boundaries": self.boundaries, # Idle gaps (> boundary threshold): normal for on-demand rendering, not a problem
            "bad_samples": self.bad_samples, # Non-positive intervals or invalid display periods (clock anomalies)
            "active_time_s": active_time_s, # Wall time spent actively rendering (sum of active intervals)
            "hitches": {
                "count": self.hitches, # Active intervals > hitch threshold — perceived stutters during animation
                "ratio": hitch_ratio, # Fraction of active intervals that were hitches
                "per_active_min": hitches_per_active_min, # Hitches normalized to time spent animating
                    # (idle time excluded)
            },
            # Distribution over ACTIVE intervals only; idle gaps never enter these numbers
            "interval_ns": {
                "avg": self.mean,
                "stddev": self.stddev(),
                "variance": self.variance(),
                "min": min_val,
                "max": max_val,
                # Percentiles are over the rolling window (last _WINDOW_SIZE intervals)
                "p50": p50,
                "p95": p95,
                "p99": p99,
            },
        }
