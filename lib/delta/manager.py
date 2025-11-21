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

from dataclasses import dataclass
from typing import Optional, List, Any
from .lap import Lap

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class DeltaToBestLapManager:
    """
    Manages multiple laps and calculates delta to best lap.
    """

    def __init__(self):
        self.laps: dict[int, Lap] = {}  # lap_number -> Lap
        self.current_lap_number: Optional[int] = None
        self.best_lap_number: Optional[int] = None

        # Cache for delta calculation optimization
        self._last_query_distance: float = -1.0
        self._cached_search_idx: int = 0

    def start_lap(self, lap_number: int):
        """
        Start a new lap (called automatically by record_data_point).
        You typically don't need to call this directly unless you want to
        pre-initialize a lap before receiving data.

        Args:
            lap_number: Lap number from sim
        """
        self.current_lap_number = lap_number
        self.laps[lap_number] = Lap(lap_number)

        # Reset delta calculation cache for new lap
        self._last_query_distance = -1.0
        self._cached_search_idx = 0

    def record_data_point(self, lap_number: int, distance: float, time: float) -> bool:
        """
        Record data point - automatically starts new lap if needed.

        This is the main entry point for telemetry data. Simply pass each packet's
        data and the manager handles lap transitions automatically.

        Args:
            lap_number: Current lap number from sim
            distance: Distance from lap start in meters
            time: Time from lap start in seconds

        Returns:
            bool: True if recorded, False if rejected (non-increasing distance)
        """
        # Auto-start new lap if lap number changed
        if lap_number != self.current_lap_number:
            self.start_lap(lap_number)

        current_lap = self.laps.get(self.current_lap_number)
        if current_lap is None:
            return False

        return current_lap.record_data_point(distance, time)

    def handle_flashback(self, new_distance: float):
        """
        Handle flashback on current lap.

        Args:
            new_distance: Distance driver rewound to
        """
        if self.current_lap_number is None:
            return

        current_lap = self.laps.get(self.current_lap_number)
        if current_lap:
            current_lap.handle_flashback(new_distance)

            # Reset cache since we've removed data points
            self._last_query_distance = -1.0
            self._cached_search_idx = 0

    def complete_current_lap(self, lap_time: float):
        """
        Mark current lap as complete.

        Args:
            lap_time: Final lap time in seconds
        """
        if self.current_lap_number is None:
            return

        current_lap = self.laps.get(self.current_lap_number)
        if current_lap:
            current_lap.complete_lap(lap_time)

    def set_best_lap(self, lap_number: int):
        """
        Set a specific lap as the best lap (from sim's determination).
        Handles case where best lap data may not be available yet.

        Args:
            lap_number: Lap number to set as best
        """
        # If lap doesn't exist yet, just record the number
        # Delta calculation will handle missing data gracefully
        self.best_lap_number = lap_number

        # Reset cache when best lap changes
        self._last_query_distance = -1.0
        self._cached_search_idx = 0

    def get_best_lap(self) -> Optional[Lap]:
        """Get the best lap object, if available"""
        if self.best_lap_number is None:
            return None
        return self.laps.get(self.best_lap_number)

    @property
    def current_lap(self) -> Optional[Lap]:
        """Get the current lap object, if available"""
        if self.current_lap_number is None:
            return None
        return self.laps.get(self.current_lap_number)

    def get_delta(self, lap_number: int, current_distance: float, current_time: float) -> Optional[float]:
        """
        Calculate delta to best lap at current position with caching optimization.

        This is the main entry point for delta queries. Simply pass each packet's
        data and get the current delta.

        Args:
            lap_number: Current lap number from sim
            current_distance: Current distance from lap start
            current_time: Current time from lap start

        Returns:
            float: Delta in seconds (positive = slower, negative = faster)
            None: If no best lap available or distance out of range
        """
        best_lap = self.get_best_lap()
        if best_lap is None:
            return None

        # Reset cache if lap number changed (new lap started)
        if lap_number != self.current_lap_number:
            self._last_query_distance = -1.0
            self._cached_search_idx = 0

        # Optimize search index based on monotonically increasing distance
        search_start_idx = 0
        if current_distance > self._last_query_distance:
            # Distance increased, start search from last position
            search_start_idx = self._cached_search_idx
        else:
            # Distance reset (new lap) or decreased (shouldn't happen in normal flow)
            search_start_idx = 0

        reference_time, new_idx = best_lap.get_time_at_distance(
            current_distance,
            search_start_idx
        )

        if reference_time is None:
            return None

        # Update cache
        self._last_query_distance = current_distance
        self._cached_search_idx = new_idx

        return current_time - reference_time

    def invalidate_lap(self, lap_number: int):
        """
        Invalidate a specific lap (track limits, contact, etc.)

        Args:
            lap_number: Lap number to invalidate
        """
        lap = self.laps.get(lap_number)
        if lap:
            lap.invalidate()

    def get_status(self) -> dict:
        """Get current status information"""
        best_lap = self.get_best_lap()
        current_lap = self.laps.get(self.current_lap_number) if self.current_lap_number else None

        return {
            'current_lap_number': self.current_lap_number,
            'best_lap_number': self.best_lap_number,
            'best_lap_available': best_lap is not None,
            'best_lap_time': best_lap.lap_time if best_lap else None,
            'best_lap_data_points': len(best_lap.data_points) if best_lap else 0,
            'current_lap_data_points': len(current_lap.data_points) if current_lap else 0,
            'current_lap_valid': current_lap.is_valid if current_lap else None,
            'total_laps': len(self.laps)
        }
