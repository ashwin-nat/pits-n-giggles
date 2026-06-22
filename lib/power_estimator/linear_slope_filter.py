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

from collections import deque

from .proto_filter import PowerFilter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LinearSlopePowerFilter(PowerFilter):
    """First-derivative power filter using a rolling least-squares linear fit.

    Estimates instantaneous power as the slope of a linear regression of energy on time over a
    rolling window: power = dE/dt. Because it fits a straight line:

    - it cannot overshoot or ring at sharp transitions (unlike a higher-order polynomial fit), and
    - on a monotonically increasing energy signal the slope is never negative.

    The regression runs against the actual timestamps, so non-uniform sample spacing (jitter,
    dropped packets) is handled exactly — no assumption of uniform cadence. Any window size of two
    or more samples is supported; larger windows smooth more at the cost of latency.
    """

    def __init__(self, window_size: int = 15) -> None:
        if window_size < 2:
            raise ValueError(f"window_size must be >= 2, got {window_size}")
        self._window_size = window_size
        self._times: deque[int] = deque(maxlen=window_size)
        self._energies: deque[float] = deque(maxlen=window_size)
        self._power_w: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, time_ms: int, energy_j: float) -> None:
        self._times.append(time_ms)
        self._energies.append(energy_j)
        if not self.is_valid():
            return

        n = self._window_size
        t_mean = sum(self._times) / n
        e_mean = sum(self._energies) / n
        # Mean-centred sums keep the slope well-conditioned even when timestamps are large
        # (lap times of tens of thousands of ms) relative to the window's time span.
        cov = sum((t - t_mean) * (e - e_mean) for t, e in zip(self._times, self._energies))
        var = sum((t - t_mean) ** 2 for t in self._times)
        if var > 0.0:
            # cov / var is energy per millisecond (J/ms); convert to watts (J/s).
            self._power_w = (cov / var) * 1000.0

    def get_power_w(self) -> float:
        return self._power_w

    def is_valid(self) -> bool:
        return len(self._times) == self._window_size

    def reset(self) -> None:
        self._times.clear()
        self._energies.clear()
        self._power_w = 0.0
