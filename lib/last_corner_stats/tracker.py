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

from lib.track_segments_classifier import TrackSegmentsDatabase
from lib.track_segments_classifier.types import (BaseSegmentInfo,
                                                  ComplexCornerSegmentInfo,
                                                  CornerSegmentInfo)

from .types import LastCornerStats, LastCornerStatsSnapshot, TelemetrySample

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

_CORNER_TYPES = (CornerSegmentInfo.TYPE, ComplexCornerSegmentInfo.TYPE)


class LastCornerTracker:
    """
    Tracks the minimum speed through the most recently completed corner (or
    complex corner), for live HUD display of "previous corner" stats.

    Public API:
      - update(circuit_pos_m: float, speed_kmph: int)
      - stats() -> LastCornerStatsSnapshot
      - reset()
    """

    def __init__(self, seg_db: TrackSegmentsDatabase) -> None:
        self._seg_db = seg_db
        self._current_segment: Optional[BaseSegmentInfo] = None
        self._current_min_speed: Optional[int] = None
        self._published: Optional[LastCornerStats] = None
        self._circuit_num: Optional[int] = None

    def update(self, sample: TelemetrySample) -> None:
        """Process one high-frequency telemetry sample."""
        if self._circuit_num is None:
            self._circuit_num = sample.circuit_num
        else:
            assert self._circuit_num == sample.circuit_num, (
                f"LastCornerTracker is bound to circuit_num={self._circuit_num}, "
                f"got {sample.circuit_num}. A circuit change implies a new session, "
                "which gets a new tracker instance - it is never expected mid-lifetime."
            )

        segment = self._seg_db.get_segment_info(sample.circuit_num, sample.circuit_pos_m)
        is_corner = segment and segment.type in _CORNER_TYPES

        if is_corner:
            if (not self._current_segment) or (self._current_segment.segment_id != segment.segment_id):
                # Entering a (new) corner: start fresh accumulation. The previously
                # published result is left in place - it's only cleared by reset().
                self._current_segment = segment
                self._current_min_speed = sample.speed_kmph
            else:
                self._current_min_speed = min(self._current_min_speed, sample.speed_kmph)
        elif self._current_segment:
            # Left the corner we were accumulating: publish it.
            self._published = LastCornerStats(
                segment=self._current_segment,
                min_speed_kmph=self._current_min_speed,
            )
            self._current_segment = None
            self._current_min_speed = None

    def stats(self) -> LastCornerStatsSnapshot:
        """Return the current tracker snapshot.

        last_pub_data holds the most recently completed corner's stats and
        stays populated across a new corner starting to accumulate - only
        reset() clears it. is_accumulating reports whether a corner is being
        driven right now, independent of last_pub_data.
        """
        return LastCornerStatsSnapshot(
            is_accumulating=self._current_segment is not None,
            last_pub_data=self._published,
        )

    def reset(self) -> None:
        """
        Clear all accumulated and published state.

        Does not clear the bound circuit_num: the circuit is a tracker-lifetime
        invariant (see update()), not corner-tracking state - a flashback or
        similar mid-session reset does not change which circuit is loaded.
        """
        self._current_segment = None
        self._current_min_speed = None
        self._published = None
