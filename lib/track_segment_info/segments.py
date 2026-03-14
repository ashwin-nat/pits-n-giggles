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

from typing import Any, Dict, List, Optional

from .types import SegmentInfo

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

class TrackSegments:
    """
    Utility class for determining track segment information from lap position.

    This class is intentionally lightweight and contains no file I/O. The caller
    is responsible for loading JSON track data and providing it via `load_track_data`.
    """

    def __init__(self) -> None:
        self._track_data: Optional[Dict[str, Any]] = None
        self._segments: List[Dict[str, Any]] = []

    def load_track_data(self, track_data: Dict[str, Any]) -> None:
        """
        Load the track knowledge base.

        Parameters
        ----------
        track_data : dict
            Raw track data loaded from JSON.

            Expected structure:

            {
                "track_length": float,
                "segments": [
                    {
                        "id": int,
                        "name": str,
                        "start_m": float,
                        "end_m": float,
                        "is_corner": bool,
                        "corner_type": str | null
                    }
                ]
            }

            Field descriptions:

            track_length
                Total circuit length in meters.

            segments
                Ordered list of track segments covering the full lap.

            id
                Unique segment identifier.

            name
                Printable name of the segment
                (e.g. "La Source", "Kemmel Straight").

            start_m
                Start distance of the segment along the lap in meters.

            end_m
                End distance of the segment along the lap in meters.

            is_corner
                True if the segment represents a corner, False if it is a straight.

            corner_type
                Optional descriptive label for the corner type
                (e.g. "hairpin_left", "high_speed", "chicane").
        """

        self._track_data = track_data
        self._segments = track_data.get("segments", [])

    def get_segment_info(self, lap_distance: float) -> Optional[SegmentInfo]:
        """
        Return the track segment corresponding to the given lap position.

        Parameters
        ----------
        lap_distance : float
            Current lap position in meters.

        Returns
        -------
        Optional[SegmentInfo]
            Strongly typed segment information if the position falls within
            a defined segment, otherwise None.
        """

        if not self._segments:
            return None

        for seg in self._segments:
            start = seg.get("start_m")
            end = seg.get("end_m")

            if start is None or end is None:
                continue

            if start <= lap_distance < end:
                return SegmentInfo(
                    segment_id=seg.get("id", -1),
                    name=seg.get("name", "Unknown Segment"),
                    is_corner=seg.get("is_corner", False),
                    corner_type=seg.get("corner_type"),
                )

        return None
