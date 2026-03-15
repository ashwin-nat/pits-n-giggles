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

from .types import CornerSegmentInfo, SegmentInfo, StraightSegmentInfo

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
        self._starts: List[float] = []  # sorted start_m values, parallel to _segments

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

            corner_number
                (corners only) Required integer corner number.

            corner_name
                (corners only) Optional human-readable corner name
                (e.g. "La Source", "Eau Rouge"). May be omitted or null.
        """

        self._track_data = track_data
        self._segments = track_data.get("segments", [])
        self._starts = [seg["start_m"] for seg in self._segments if "start_m" in seg]

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

        if not self._starts:
            return None

        # Find the rightmost segment whose start_m <= lap_distance
        idx = bisect.bisect_right(self._starts, lap_distance) - 1
        if idx < 0:
            return None

        seg = self._segments[idx]
        if lap_distance >= seg.get("end_m", float("-inf")):
            return None

        seg_id = seg.get("id", -1)
        if seg.get("is_corner", False):
            return CornerSegmentInfo(
                segment_id=seg_id,
                corner_number=seg["corner_number"],
                corner_name=seg.get("corner_name"),
            )
        return StraightSegmentInfo(
            segment_id=seg_id,
            name=seg.get("name", "Unknown Straight"),
        )
