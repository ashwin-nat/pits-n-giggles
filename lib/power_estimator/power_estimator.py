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

from typing import Optional

from .savgol_filter import SavGolPowerFilter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PowerEstimator:
    """High-level manager that owns a filter and handles continuity lifecycle.

    Detects time regressions and lap transitions, resetting the filter when
    continuity is broken so previous history never influences future output.

    The underlying filter implementation is an internal detail. Callers configure
    it via the constructor parameters rather than supplying a filter instance.
    """

    def __init__(self, window_size: int = 15, polynomial_order: int = 3) -> None:
        """
        Args:
            window_size:      Rolling sample window passed to the internal filter.
                              Larger values increase smoothing at the cost of latency.
                              Must be one of the supported configurations (9, 15, 21).
                              Defaults to 15 — balanced for ~60 Hz input cadence.
            polynomial_order: Polynomial fit order for the internal filter. Defaults to 3.
        """
        self._filter = SavGolPowerFilter(window_size, polynomial_order)
        self._last_time_ms: Optional[int] = None
        self._last_lap: Optional[int] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, time_ms: int, energy_j: float, lap_number: Optional[int] = None) -> None:
        """Consume a new sample, resetting the filter if continuity is broken.

        Continuity is considered broken when:
        - ``time_ms`` is less than or equal to the previous timestamp (regression or duplicate), or
        - ``lap_number`` changes between calls (both must be non-None to trigger this).

        Args:
            time_ms:    Monotonic timestamp in milliseconds.
            energy_j:   Cumulative energy in joules.
            lap_number: Optional lap counter used as a continuity hint. A change
                        in value triggers a filter reset. Pass ``None`` to disable
                        lap-based reset detection.
        """
        if self._last_time_ms is not None:
            time_regressed = time_ms <= self._last_time_ms
            lap_changed = (
                lap_number is not None
                and self._last_lap is not None
                and lap_number != self._last_lap
            )
            if time_regressed or lap_changed:
                self._filter.reset()

        self._last_time_ms = time_ms
        self._last_lap = lap_number
        self._filter.update(time_ms, energy_j)

    def get_power_w(self) -> float:
        """Return the latest estimated power in watts.

        Returns 0.0 when the filter has not yet warmed up or has been reset.
        Does not mutate any state.
        """
        return self._filter.get_power_w()

    def is_valid(self) -> bool:
        """Return True when the filter has sufficient history to produce meaningful output."""
        return self._filter.is_valid()

    def reset(self) -> None:
        """Reset the filter and clear all continuity tracking state.

        After this call ``is_valid()`` returns False and the next ``update()``
        starts a fresh continuous segment.
        """
        self._filter.reset()
        self._last_time_ms = None
        self._last_lap = None
