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

from typing import Tuple, Optional, List
from .data import LapDataPoint
import bisect

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class Lap:
    """
    Represents a single lap with telemetry data and convenience methods.
    """

    def __init__(self, lap_number: int):
        self.lap_number = lap_number
        self.data_points: List[LapDataPoint] = []
        self.lap_time: Optional[float] = None
        self.is_valid: bool = True
        self._last_distance: float = -1.0

    def record_data_point(self, distance: float, time: float) -> bool:
        """
        Record a telemetry data point.

        Args:
            distance: Distance from lap start in meters
            time: Time from lap start in seconds

        Returns:
            bool: True if recorded, False if rejected (distance didn't increase)
        """
        if distance <= self._last_distance:
            return False

        self.data_points.append(LapDataPoint(distance, time))
        self._last_distance = distance
        return True

    def handle_flashback(self, new_distance: float):
        """
        Remove all data points beyond new_distance after a flashback.
        Marks lap as invalid.

        Args:
            new_distance: The distance the driver rewound to
        """
        self.is_valid = False

        # Binary search to find cutoff point
        cutoff_idx = bisect.bisect_right(
            [p.distance for p in self.data_points],
            new_distance
        )

        self.data_points = self.data_points[:cutoff_idx]

        # Update last distance tracker
        if self.data_points:
            self._last_distance = self.data_points[-1].distance
        else:
            self._last_distance = -1.0

    def complete_lap(self, lap_time: float):
        """
        Mark lap as complete with final time.

        Args:
            lap_time: Total lap time in seconds
        """
        self.lap_time = lap_time

    def get_time_at_distance(self, distance: float, search_start_idx: int = 0) -> Tuple[Optional[float], int]:
        """
        Get interpolated time at a specific distance.

        Args:
            distance: Distance to query
            search_start_idx: Index to start binary search from (optimization)

        Returns:
            Tuple of (interpolated_time, search_index_used)
            Returns (None, search_start_idx) if distance is out of range
        """
        if not self.data_points or len(self.data_points) < 2:
            return None, search_start_idx

        # Check if beyond recorded distance
        if distance > self.data_points[-1].distance:
            return None, search_start_idx

        # Binary search starting from search_start_idx
        distances = [p.distance for p in self.data_points[search_start_idx:]]
        relative_idx = bisect.bisect_left(distances, distance)
        idx = search_start_idx + relative_idx

        # Handle edge cases
        if idx == 0:
            return self.data_points[0].time, 0

        if idx >= len(self.data_points):
            return self.data_points[-1].time, len(self.data_points) - 1

        # Linear interpolation between two points
        p1 = self.data_points[idx - 1]
        p2 = self.data_points[idx]

        distance_fraction = (distance - p1.distance) / (p2.distance - p1.distance)
        interpolated_time = p1.time + distance_fraction * (p2.time - p1.time)

        return interpolated_time, max(0, idx - 1)

    def invalidate(self):
        """Mark lap as invalid (e.g., track limits, contact)"""
        self.is_valid = False
