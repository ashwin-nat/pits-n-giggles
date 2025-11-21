

# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

import bisect
from typing import Dict, List, Optional, Tuple

from .data import DeltaResult, LapPoint

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapDeltaManager:
    """
    Maintains lap distance/time samples and computes delta relative to a chosen best lap.

    HOLY PRINCIPLE: Distances within a lap are strictly monotonic. If a new data point arrives with
    distance <= last distance, future samples are dropped and the new point replaces them.

    Public API:
      - record_data_point(lap_num: int, curr_distance: float, curr_time_ms: int)
      - set_best_lap(lap_num: int)
      - get_delta() -> Optional[DeltaResult]
      - handle_flashback(lap_num: int, curr_distance: float)
    """

    def __init__(self) -> None:
        self._laps: Dict[int, List[LapPoint]] = {}
        self._lap_distances: Dict[int, List[float]] = {}

        self._best_lap_num: Optional[int] = None
        self._last_recorded_point: Optional[LapPoint] = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def record_data_point(self, lap_num: int, curr_distance: float, curr_time_ms: int) -> None:
        """
        Insert a new data point while maintining the HOLY PRINCIPLE.
        - If curr_distance > last_distance: append normally.
        - Else: drop all points with distance >= curr_distance and insert this point.
        """

        # Setup lap if it doesn't exist
        if lap_num not in self._laps:
            self._laps[lap_num] = []
            self._lap_distances[lap_num] = []

        pts = self._laps[lap_num]
        dists = self._lap_distances[lap_num]

        if not pts:
            # New lap, simple case
            p = LapPoint(lap_num, curr_distance, curr_time_ms)
            pts.append(p)
            dists.append(curr_distance)
            self._last_recorded_point = p
            return

        last_dist = dists[-1]
        if curr_distance > last_dist:
            # Normal case - incoming data point is after last recorded point
            p = LapPoint(lap_num, curr_distance, curr_time_ms)
            pts.append(p)
            dists.append(curr_distance)
            self._last_recorded_point = p
            return

        # -----------------------------------------------------------------
        # Timeline rewrite block - incoming data is violating the HOLY PRINCIPLE
        # Drop all points with dist >= curr_distance and insert replacement.
        # -----------------------------------------------------------------
        drop_idx = bisect.bisect_left(dists, curr_distance)

        del pts[drop_idx:]
        del dists[drop_idx:]

        p = LapPoint(lap_num, curr_distance, curr_time_ms)
        pts.append(p)
        dists.append(curr_distance)
        self._last_recorded_point = p

    def set_best_lap(self, lap_num: int) -> None:
        """
        Set the lap number that should be used as the 'best lap' reference.

        The caller may set a lap for which we don't yet have data; that's allowed.
        """
        self._best_lap_num = lap_num

    def get_delta(self) -> Optional[DeltaResult]:
        """
        Compute delta (current_time_ms - best_time_ms_at_same_distance) for the latest recorded point.

        Returns None when:
          - no best lap set
          - no last recorded point
          - best lap has no data or does not cover the distance of the current point
        """
        if self._best_lap_num is None:
            return None
        if self._last_recorded_point is None:
            return None

        best = self._best_lap_num
        if best not in self._laps or not self._laps[best]:
            return None

        curr = self._last_recorded_point
        best_time = self._interpolated_time_for_distance(best, curr.distance_m)
        if best_time is None:
            return None
        return DeltaResult(
            delta_ms=(curr.time_ms - best_time),
            curr_point=curr,
            best_lap_num=best,
            best_time_ms_at_distance=best_time,
            distance_m=curr.distance_m,
        )

    def handle_flashback(self, lap_num: int, curr_distance: float) -> None:
        """
        Handle a simulator flashback (rewind) event. This cleans up the old outdated data because
        they will certainly violate the HOLY PRINCIPLE.

        Behavior:
        - All laps with numbers greater than `lap_num` are deleted. These laps
            represent a future timeline that no longer exists after the rewind.
        - The target lap (`lap_num`) is trimmed so that only points with
            distance < `curr_distance` remain. Any point at or beyond this distance
            belongs to the discarded future timeline.
        - A synthetic point `(curr_distance, time_ms=0)` is appended to the
            trimmed lap to represent the new rewind position. The next real
            telemetry update will overwrite or advance from this anchor point.
        - `_last_recorded_point` is updated to this newly inserted synthetic
            point.

        This method performs direct mutation of lap storage and does not use
        `record_data_point()`, because record_data_point applies its own rewrite
        semantics intended only for forward telemetry flow.
        """
        # remove future laps
        for ln in list(self._laps.keys()):
            if ln > lap_num:
                del self._laps[ln]
                del self._lap_distances[ln]

        # ensure lap exists
        if lap_num not in self._laps:
            self._laps[lap_num] = []
            self._lap_distances[lap_num] = []

        # trim current lap
        pts = self._laps[lap_num]
        dists = self._lap_distances[lap_num]
        idx = bisect.bisect_left(dists, curr_distance)
        del pts[idx:]
        del dists[idx:]

        # insert flashback point directly
        p = LapPoint(lap_num, curr_distance, 0)
        pts.append(p)
        dists.append(curr_distance)
        self._last_recorded_point = p

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _interpolated_time_for_distance(self, lap_num: int, distance: float) -> Optional[float]:
        """
        Return interpolated time (float ms) for given distance on lap_num.

        Returns None if lap doesn't exist or doesn't cover the distance (i.e., distance outside recorded span).
        """
        dists = self._lap_distances.get(lap_num)
        pts = self._laps.get(lap_num)

        if not dists:
            return None

        if distance < dists[0] or distance > dists[-1]:
            return None

        idx = bisect.bisect_left(dists, distance)

        if idx < len(dists) and dists[idx] == distance:
            return pts[idx].time_ms

        lo = idx - 1
        hi = idx

        d_lo = dists[lo]
        d_hi = dists[hi]
        t_lo = pts[lo].time_ms
        t_hi = pts[hi].time_ms

        if d_hi == d_lo:
            return t_lo

        ratio = (distance - d_lo) / (d_hi - d_lo)
        return t_lo + ratio * (t_hi - t_lo)

    def _dump_state(self) -> Dict[int, List[Tuple[float, int]]]:
        """Return a serializable snapshot for debugging: lap_num -> list of (distance, time_ms)."""
        return {
            lap_num: [(p.distance_m, p.time_ms) for p in pts]
            for lap_num, pts in self._laps.items()
        }
