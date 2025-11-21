

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
    Encapsulates recording lap points and computing delta vs a chosen 'best lap'.

    Public API:
      - record_data_point(lap_num: int, curr_distance: float, curr_time_ms: int)
      - set_best_lap(lap_num: int)
      - get_delta() -> Optional[DeltaResult]
      - handle_flashback(lap_num: int, curr_distance: float)
    """

    def __init__(self) -> None:
        # lap_num -> sorted list of LapPoint (sorted by distance_m ascending)
        self._laps: Dict[int, List[LapPoint]] = {}
        # quick caches of distances for bisecting: lap_num -> list of distances (monotonic)
        self._lap_distances: Dict[int, List[float]] = {}

        # the lap number designated as the 'best lap' by caller (or None)
        self._best_lap_num: Optional[int] = None

        # the latest LapPoint recorded by record_data_point (or None)
        self._last_recorded_point: Optional[LapPoint] = None

    # -------------------------
    # Public API
    # -------------------------
    def record_data_point(self, lap_num: int, curr_distance: float, curr_time_ms: int) -> None:
        """
        Record a datapoint.

        - Automatically creates the lap bank if needed.
        - Drops (ignores) points whose distance is <= last recorded distance for the same lap.
          This handles backing-up/spin scenarios.
        - Does not attempt to detect flashbacks (call handle_flashback if a rewind happened).
        """
        if lap_num not in self._laps:
            self._laps[lap_num] = []
            self._lap_distances[lap_num] = []

        last_for_lap = self._laps[lap_num][-1] if self._laps[lap_num] else None

        # Drop backwards motion on same lap: ignore new point if distance <= last distance.
        if last_for_lap is not None and curr_distance <= last_for_lap.distance_m:
            # intentional drop
            return

        point = LapPoint(lap_num=lap_num, distance_m=float(curr_distance), time_ms=int(curr_time_ms))
        # preserve monotonic sorted distances by appending (we assume distance increases within a lap)
        self._laps[lap_num].append(point)
        self._lap_distances[lap_num].append(point.distance_m)

        self._last_recorded_point = point

    def set_best_lap(self, lap_num: int) -> None:
        """
        Set the lap number that should be used as the 'best lap' reference.

        The caller may set a lap for which we don't yet have data; that's allowed.
        """
        self._best_lap_num = int(lap_num)

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

        best_num = self._best_lap_num
        if best_num not in self._laps or not self._laps[best_num]:
            # we don't yet have data for the best lap
            return None

        curr = self._last_recorded_point
        # find interpolated time on best lap at curr.distance_m
        best_time = self._interpolated_time_for_distance(best_num, curr.distance_m)
        if best_time is None:
            # best lap doesn't have coverage for this distance (start/end missing)
            return None

        delta_ms = int(curr.time_ms) - int(best_time)
        return DeltaResult(
            delta_ms=delta_ms,
            curr_point=curr,
            best_lap_num=best_num,
            best_time_ms_at_distance=int(best_time),
            distance_m=curr.distance_m,
        )

    def handle_flashback(self, lap_num: int, curr_distance: float) -> None:
        """
        Handle a flashback (rewind) issued by the simulator.

        Two different behaviors exist:

        1. LAP REWIND (lap_num < previously recorded lap):
            - Delete all recorded data for future laps.
            - On the target lap, keep all points whose distance <= curr_distance.
            (Because the rewind lands *on or after* that position in the past.)

        2. SAME-LAP FLASHBACK (lap_num == current lap):
            - We rewound to a point *before* curr_distance.
            - All points whose distance >= curr_distance belong to the "future timeline"
            and must be removed.
            - Keep only points strictly less than curr_distance.
            - The next record_data_point() call will insert a new point at exactly curr_distance.

        After trimming, update _last_recorded_point to the last point in time order.
        """

        lap_num = int(lap_num)
        curr_distance = float(curr_distance)

        # --- Detect lap rewind: any lap greater than target must be removed ---
        future_laps = [ln for ln in list(self._laps.keys()) if ln > lap_num]
        is_lap_rewind = len(future_laps) > 0

        for ln in future_laps:
            del self._laps[ln]
            del self._lap_distances[ln]

        # Ensure lap storage exists
        if lap_num not in self._laps:
            self._laps[lap_num] = []
            self._lap_distances[lap_num] = []

        pts = self._laps[lap_num]
        dists = self._lap_distances[lap_num]

        if dists:

            if is_lap_rewind:
                # LAP REWIND:
                # Keep points <= curr_distance
                # LAP-REWIND FLASHBACK (lap number decreases)
                # -------------------------------------------
                #
                # Suppose we have recorded:
                #
                #     Lap 1:   10 ---- 20 ---- 30 ---- 40 ---- 50
                #                p1     p2     p3     p4     p5
                #
                #     Lap 2:   15 ---- 25 ---- 35
                #                q1     q2     q3
                #
                # And the user flashbacks to:
                #     lap_num = 1
                #     curr_distance = 22
                #
                # Step 1: Remove all laps > 1, since they are "future timeline":
                #     Lap 2 is deleted.
                #
                # Step 2: In lap 1, keep points whose distance <= 22.
                #     10, 20 remain.
                #     30, 40, 50 are removed.
                #
                # Final state after flashback:
                #     Lap 1:   10 ---- 20
                #                p1     p2
                #
                # Next telemetry update will continue from this rewound position.

                idx = bisect.bisect_right(dists, curr_distance)
                self._laps[lap_num] = pts[:idx]
                self._lap_distances[lap_num] = dists[:idx]

            else:
                # SAME-LAP FLASHBACK:
                # Discard points >= curr_distance
                # SAME-LAP FLASHBACK (curr_distance = X)
                # --------------------------------------
                #
                # We have a timeline of recorded points in a lap, sorted by distance:
                #
                #     Before flashback:
                #         10 ---- 20 ---- 30 ---- 40 ---- 50
                #          p1     p2     p3     p4     p5
                #
                # If the flashback happens at distance X = 25:
                #
                #     We drop ALL points whose distance >= 25:
                #         - drop p3 (30)
                #         - drop p4 (40)
                #         - drop p5 (50)
                #
                #     Keep only points whose distance < 25:
                #         10 ---- 20
                #          p1     p2
                #
                # After the flashback, the next telemetry update from the sim will be:
                #         distance = 25
                # and record_data_point() will accept it because 25 > 20.
                #
                # Final state after flashback:
                #         10 ---- 20
                #          p1     p2

                new_pts = []
                new_dists = []
                for p, d in zip(pts, dists):
                    if d < curr_distance:
                        new_pts.append(p)
                        new_dists.append(d)
                self._laps[lap_num] = new_pts
                self._lap_distances[lap_num] = new_dists

        # Refresh last recorded point
        all_points = self._all_points_sorted_by_time_order()
        self._last_recorded_point = all_points[-1] if all_points else None

    # -------------------------
    # Internal helpers (private)
    # -------------------------
    def _interpolated_time_for_distance(self, lap_num: int, distance: float) -> Optional[float]:
        """
        Return interpolated time (float ms) for given distance on lap_num.

        Returns None if lap doesn't exist or doesn't cover the distance (i.e., distance outside recorded span).
        """
        if lap_num not in self._laps or not self._laps[lap_num]:
            return None

        distances = self._lap_distances[lap_num]
        pts = self._laps[lap_num]

        # If exactly matches first or last
        if distance < distances[0] or distance > distances[-1]:
            return None

        # bisect to find right index
        idx = bisect.bisect_left(distances, distance)
        if idx < len(distances) and distances[idx] == distance:
            return float(pts[idx].time_ms)

        # interpolate between idx-1 and idx
        # after bisect_left, idx is insertion position, so idx>0 guaranteed because distance >= distances[0]
        hi = idx
        lo = idx - 1
        d_lo = distances[lo]
        d_hi = distances[hi]
        t_lo = pts[lo].time_ms
        t_hi = pts[hi].time_ms

        # This cannot happen due to strict monotonic distances enforced in record_data_point,
        # but we keep it as a safety fallback.
        if d_hi == d_lo: # pragma: no cover
            # degenerate; return lower time
            return float(t_lo)

        # linear interpolation
        ratio = (distance - d_lo) / (d_hi - d_lo)
        interp_time = t_lo + ratio * (t_hi - t_lo)
        return float(interp_time)

    def _all_points_sorted_by_time_order(self) -> List[LapPoint]:
        """
        Returns a stable ordering for all points that reflects the order recorded.
        We rely on the per-lap lists being appended in chronological order; combine them in ascending lap_num order.
        Note: if the sim reports lap numbers out-of-order and caller didn't flashback, ordering is 'best-effort'.
        """
        out: List[LapPoint] = []
        for ln in sorted(self._laps.keys()):
            out.extend(self._laps[ln])
        return out

    # -------------------------
    # Optional helpers for debugging / inspection (not part of 'required' API)
    # -------------------------
    def _dump_state(self) -> Dict[int, List[Tuple[float, int]]]:
        """Return a serializable snapshot for debugging: lap_num -> list of (distance, time_ms)."""
        return {ln: [(p.distance_m, p.time_ms) for p in pts] for ln, pts in self._laps.items()}
