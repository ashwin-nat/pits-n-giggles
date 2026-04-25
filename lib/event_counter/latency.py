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
_EWMA_ALPHA: float = 0.1

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------


@dataclass(slots=True)
class LatencyStat(Stat):
    """Latency distribution tracker for packet timing.

    Tracks:
        - `count`: number of valid latency samples used in the model.
        - `bad_latency_count`: number of invalid samples (negative latency).
        - `min` / `max`: extrema of valid latencies.
        - `avg` / `variance`: running population statistics of valid latencies.
        - `stddev`: running population standard deviation of valid latencies.
        - `p50_ns` / `p95_ns` / `p99_ns`: percentiles over a rolling window.
        - `jitter_avg_ns` / `jitter_max_ns`: inter-sample variability.
        - `ewma_ns`: exponential weighted moving average.
        - `tail_ratio`: p99 / p50.
    """

    TYPE: ClassVar[str] = "__LATENCY__"

    min: int = 2**63 - 1
    max: int = 0
    bad_latency_count: int = 0

    mean: float = 0.0
    m2: float = 0.0

    # Rolling window for percentile computation (O(1) append, computed at read time).
    samples: deque = field(default_factory=lambda: deque(maxlen=_WINDOW_SIZE))

    # Jitter: |current - previous| latency.
    prev_latency: int = -1
    jitter_sum: float = 0.0
    jitter_count: int = 0
    jitter_max: int = 0

    # EWMA: initialised on first valid sample (sentinel -1.0 = uninitialised).
    ewma: float = -1.0

    def observe_packet(self, sender_ts_ns: int, recv_ts_ns: int) -> None:
        """Observe one packet timing sample and update running latency stats.

        Negative latency samples are counted as bad data and ignored.
        All operations are O(1) and allocation-free after initialisation.
        """
        latency = recv_ts_ns - sender_ts_ns

        # Guard against rare clock adjustments: track bad samples but
        # do not let them influence min/max/mean/variance.
        if latency < 0:
            self.bad_latency_count += 1
            return

        self.count += 1

        self.min = min(self.min, latency)
        self.max = max(self.max, latency)

        # Welford running mean/variance
        delta = latency - self.mean
        self.mean += delta / self.count
        delta2 = latency - self.mean
        self.m2 += delta * delta2

        # Rolling window (O(1) deque append, maxlen enforces fixed size)
        self.samples.append(latency)

        # Jitter: requires at least one prior sample
        if self.prev_latency >= 0:
            jitter = abs(latency - self.prev_latency)
            self.jitter_sum += jitter
            self.jitter_count += 1
            self.jitter_max = max(self.jitter_max, jitter)
        self.prev_latency = latency

        # EWMA: initialise on first sample, smooth thereafter
        if self.ewma < 0:
            self.ewma = float(latency)
        else:
            self.ewma = _EWMA_ALPHA * latency + (1.0 - _EWMA_ALPHA) * self.ewma

    def variance(self) -> float:
        """Return population variance of valid latency samples."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    def stddev(self) -> float:
        """Return population standard deviation of valid latency samples."""
        return math.sqrt(self.variance())

    def to_dict(self) -> dict:
        """Serialize this latency stat to a JSON-friendly dictionary.

        Percentile computation (sort) happens here, not in the hot path.
        """
        min_val = self.min if self.count > 0 else 0
        max_val = self.max if self.count > 0 else 0

        # Percentiles: sort the rolling window snapshot once
        n = len(self.samples)
        if n > 0:
            sorted_samples = sorted(self.samples)
            p50 = sorted_samples[int((n - 1) * 0.50)]
            p95 = sorted_samples[int((n - 1) * 0.95)]
            p99 = sorted_samples[int((n - 1) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        tail_ratio = (p99 / p50) if p50 > 0 else 0.0
        jitter_avg = (self.jitter_sum / self.jitter_count) if self.jitter_count > 0 else 0.0
        ewma_val = self.ewma if self.ewma >= 0.0 else 0.0

        return {
            "type": self.TYPE,
            "count": self.count,
            "bad_latency_count": self.bad_latency_count,
            "min_ns": min_val,
            "max_ns": max_val,
            "avg_ns": self.mean,
            "variance_ns": self.variance(),
            "stddev_ns": self.stddev(),
            "p50_ns": p50,
            "p95_ns": p95,
            "p99_ns": p99,
            "jitter_avg_ns": jitter_avg,
            "jitter_max_ns": self.jitter_max,
            "ewma_ns": ewma_val,
            "tail_ratio": tail_ratio,
        }
