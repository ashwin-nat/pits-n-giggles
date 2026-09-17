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

import bisect
from typing import Any, Dict, List, Optional

from lib.f1_types.packet_2_lap_data import LapData

from .types import BaseSegmentInfo, SectorBoundaries, TrackData

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

class TrackSegmentsClassifier:
    """
    Utility class for determining track segment information from lap position.

    This class is intentionally lightweight and contains no file I/O. The caller
    is responsible for loading JSON track data and providing it via `load_track_data`.
    """

    def __init__(self) -> None:
        self._track_data: Optional[TrackData] = None
        self._segments: List[BaseSegmentInfo] = []
        self._starts: List[float] = []  # sorted start_m values, parallel to _segments
        self._last_segment: Optional[BaseSegmentInfo] = None # Cache

    @property
    def circuit_name(self) -> Optional[str]:
        return self._track_data.circuit_name if self._track_data else None

    @property
    def circuit_number(self) -> Optional[int]:
        return self._track_data.circuit_number if self._track_data else None

    def load_track_data(self, track_data: Dict[str, Any]) -> None:
        """
        Load the track knowledge base.

        Parameters
        ----------
        track_data : dict
            Raw track data loaded from JSON.

            Expected structure:

            {
                "circuit_name":   str,           (required)
                "circuit_number": int,           (required)
                "track_length":   float,         (required)
                "segments": [
                    {
                        "type": str,
                        "name": str,
                        "start_m": float,
                        "end_m": float,
                        ...type-specific fields...
                    }
                ],
                "sectors": {                     (optional)
                    "s1": int,                   (required if sectors present; must be > 0)
                    "s2": int,                   (required if sectors present; must be > s1 and < track_length)
                }
            }

            Segments must be ordered by start_m and must not overlap.

            Segment types:

            straight
                No additional fields.

            corner
                corner_number : int  (required)

            complex_corner
                corner_numbers : list[int]  (required)
        """

        self._track_data = TrackData.model_validate(track_data)
        self._segments = list(self._track_data.segments)
        self._starts = [seg.start_m for seg in self._segments]
        self._last_segment = None

    @property
    def sectors(self) -> Optional[SectorBoundaries]:
        """Return the sector boundaries for this track, or None if not defined."""
        if self._track_data is None:
            return None
        return self._track_data.sectors

    def get_segment_info(self, lap_distance: float) -> Optional[BaseSegmentInfo]:
        """
        Return the track segment corresponding to the given lap position.

        Requires `load_track_data` to have been called first; there is no
        meaningful segment lookup on an unloaded classifier.

        Parameters
        ----------
        lap_distance : float
            Current lap position in meters. May be negative or exceed
            track_length (e.g. sim-emitted values during outlaps); the
            position is normalized onto the lap before lookup.

        Returns
        -------
        Optional[BaseSegmentInfo]
            Strongly typed segment information if the position falls within
            a defined segment, otherwise None.
        """
        norm_dist = self._normalize_lap_distance(lap_distance)
        if self._last_segment and self._last_segment.contains(norm_dist):
            return self._last_segment
        self._last_segment = self._get_segment_info_impl(norm_dist)
        return self._last_segment

    def get_sector(self, lap_distance: float) -> Optional[LapData.Sector]:
        """
        Return the sector corresponding to the given lap position.

        Requires `load_track_data` to have been called first (this returns
        None gracefully rather than asserting, since sector data is optional
        even when a track is loaded).

        Parameters
        ----------
        lap_distance : float
            Current lap position in meters.

        Returns
        -------
        Optional[LapData.Sector]
            The sector if the position falls within a defined sector boundary,
            otherwise None (no sector data loaded, or position is beyond s3).
        """

        if self._track_data is None or self._track_data.sectors is None:
            return None

        s = self._track_data.sectors
        track_length = self._track_data.track_length
        norm_dist = self._normalize_lap_distance(lap_distance)
        if norm_dist == track_length:
            norm_dist = 0
        if 0 <= norm_dist < s.s1:
            return LapData.Sector.SECTOR1
        if s.s1 <= norm_dist < s.s2:
            return LapData.Sector.SECTOR2
        if s.s2 <= norm_dist < track_length:
            return LapData.Sector.SECTOR3
        return None

    def _get_segment_info_impl(self, lap_distance: float) -> Optional[BaseSegmentInfo]:
        if not self._starts:
            return None

        # Find the rightmost segment whose start_m <= lap_distance
        idx = bisect.bisect_right(self._starts, lap_distance) - 1
        if idx < 0:
            return None

        seg = self._segments[idx]
        if lap_distance >= seg.end_m:
            return None

        return seg

    def _normalize_lap_distance(self, lap_distance: float) -> float:
        """
        Normalize lap distance to the range [0, track_length).

        Sim telemetry legitimately emits negative lap_distance values during
        outlaps, and values can also land exactly on/just past track_length
        at the start/finish line; both wrap onto the lap rather than being
        treated as out-of-range.
        """
        assert self._track_data and self._track_data.track_length, (
            "load_track_data() must be called before any get_* lookup"
        )
        track_length = self._track_data.track_length
        return lap_distance % track_length
