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
from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lib.f1_types.packet_2_lap_data import LapData

from .types import (ComplexCornerSegmentInfo, CornerSegmentInfo,
                    SectorBoundaries, SegmentInfo)

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

@dataclass(slots=True)
class CacheState:
    """Last-hit segment memo. Internal to TrackSegmentsClassifier."""
    last: Optional[SegmentInfo] = None


class TrackSegmentsClassifier(BaseModel):
    """
    Validated track segment data for one circuit, plus distance-to-segment lookup.

    Build with `TrackSegmentsClassifier.model_validate({...json..., "use_cache": bool})`.

    Fields
    ------
    circuit_name, circuit_number, track_length : circuit identity
    segments : ordered, non-overlapping segments (straight / corner / complex_corner)
    sectors : optional sector boundaries; must satisfy s1 < s2 < track_length
    use_cache : required. True memoizes the last hit, which helps a single car moving
        along the track and hurts random access (e.g. looking up many cars).
    """

    model_config = ConfigDict(frozen=True)

    circuit_name: str
    circuit_number: int
    track_length: float
    segments: List[SegmentInfo]
    sectors: Optional[SectorBoundaries] = None
    use_cache: bool

    # Cache is a dataclass because pydantic has a custom __setattr__ that has a significant performance penalty
    # This way, since the cache property is not being directly set by the user, we can avoid the overhead penalty
    cache: CacheState = Field(default_factory=CacheState, exclude=True)

    @model_validator(mode="after")
    def _check_sectors_within_track(self) -> "TrackSegmentsClassifier":
        if self.sectors is not None and self.sectors.s2 >= self.track_length:
            raise ValueError(
                f"sectors.s2 ({self.sectors.s2}) must be less than track_length ({self.track_length})"
            )
        return self

    @model_validator(mode="after")
    def _check_segments(self) -> "TrackSegmentsClassifier":
        """Cross-segment checks: order, overlap, lap bounds and corner numbering."""
        segments = self.segments
        for i, curr in enumerate(segments):
            if curr.start_m < 0:
                raise ValueError(f"segment {i} starts before the lap: start_m={curr.start_m} < 0")
            if curr.end_m > self.track_length:
                raise ValueError(
                    f"segment {i} ends past the lap: end_m={curr.end_m} > track_length={self.track_length}"
                )
            if i == 0:
                continue
            prev = segments[i - 1]
            if curr.start_m < prev.start_m:
                raise ValueError(
                    f"segment {i} is out of order: start_m={curr.start_m} < previous start_m={prev.start_m}"
                )
            if curr.start_m < prev.end_m:
                raise ValueError(
                    f"segment {i} overlaps previous: start_m={curr.start_m} < previous end_m={prev.end_m}"
                )

        # Corner and complex_corner numbers are counted together, in lap order
        expected = 1
        for seg in segments:
            if isinstance(seg, CornerSegmentInfo):
                numbers: Sequence[int] = (seg.corner_number,)
            elif isinstance(seg, ComplexCornerSegmentInfo):
                numbers = seg.corner_numbers
            else:
                continue
            for num in numbers:
                if num == expected:
                    expected += 1
                elif num < expected:
                    raise ValueError(
                        f"corner {num} at {seg.start_m}m is a duplicate or out of order (expected {expected})"
                    )
                else:
                    missing = ", ".join(str(n) for n in range(expected, num))
                    raise ValueError(
                        f"corner numbers must start at 1 and have no gaps: missing {missing} before corner {num}"
                    )
        return self

    # Field validator rather than post-init: the model is frozen, so segments can't be reassigned afterwards.
    # segment_id is the segment's index in the array.
    @field_validator("segments", mode="after")
    @classmethod
    def _stamp_segment_ids(cls, segments: List[SegmentInfo]) -> List[SegmentInfo]:
        return [seg.model_copy(update={"segment_id": idx}) for idx, seg in enumerate(segments)]

    @cached_property
    def starts(self) -> List[float]:
        """Segment start_m values, parallel to `segments`, for bisect."""
        return [seg.start_m for seg in self.segments]

    def get_segment_info(self, lap_distance: float) -> Optional[SegmentInfo]:
        """
        Return the segment containing the given lap position, or None if it falls in an
        undefined gap. Negative or >= track_length values (outlaps, start/finish) are
        wrapped onto the lap first.
        """
        norm_dist = lap_distance % self.track_length
        if self.use_cache:
            last = self.cache.last
            if last is not None and last.start_m <= norm_dist < last.end_m:
                return last
            seg = self._lookup(norm_dist)
            self.cache.last = seg
            return seg
        return self._lookup(norm_dist)

    def get_sector(self, lap_distance: float) -> Optional[LapData.Sector]:
        """
        Return the sector containing the given lap position, or None if this circuit
        has no sector data.
        """
        s = self.sectors
        if s is None:
            return None

        norm_dist = lap_distance % self.track_length
        if norm_dist < s.s1:
            return LapData.Sector.SECTOR1
        if norm_dist < s.s2:
            return LapData.Sector.SECTOR2
        return LapData.Sector.SECTOR3

    def _lookup(self, norm_dist: float) -> Optional[SegmentInfo]:
        # Rightmost segment whose start_m <= norm_dist; end_m is exclusive
        idx = bisect.bisect_right(self.starts, norm_dist) - 1
        if idx < 0:
            return None
        seg = self.segments[idx]
        if norm_dist >= seg.end_m:
            return None
        return seg
