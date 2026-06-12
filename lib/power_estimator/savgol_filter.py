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

from .base_filter import BasePowerFilter
from ._coefficients import SAVGOL_COEFFS

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SavGolPowerFilter(BasePowerFilter):
    """Savitzky-Golay first-derivative power filter using precomputed coefficients.

    Estimates instantaneous power via a rolling polynomial fit over energy samples.
    Assumes approximately uniform sample spacing; scales by the observed average dt.
    """

    def __init__(self, window_size: int, polynomial_order: int = 3) -> None:
        key = (window_size, polynomial_order)
        if key not in SAVGOL_COEFFS:
            supported = sorted(SAVGOL_COEFFS.keys())
            raise ValueError(f"Unsupported SavGol configuration {key}. Supported: {supported}")
        self._coeffs: list[float] = SAVGOL_COEFFS[key]
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
        if self.is_valid():
            avg_dt_ms = (self._times[-1] - self._times[0]) / (self._window_size - 1)
            if avg_dt_ms > 0.0:
                d_energy = sum(c * e for c, e in zip(self._coeffs, self._energies))
                # d_energy is in joules/sample; convert to watts (J/s)
                self._power_w = d_energy * 1000.0 / avg_dt_ms

    def get_power_w(self) -> float:
        return self._power_w

    def is_valid(self) -> bool:
        return len(self._times) == self._window_size

    def reset(self) -> None:
        self._times.clear()
        self._energies.clear()
        self._power_w = 0.0
