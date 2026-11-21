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
from typing import Any, Dict, Iterator, Literal, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lib.f1_types.packet_2_lap_data import LapData

from .types import (ActiveAeroZoneInfo, ComplexCornerSegmentInfo,
                    CornerSegmentInfo, DrsZoneInfo, OvertakeZoneInfo,
                    SectorBoundaries, SegmentInfo, _num)

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
    sectors : sector boundaries (required); must satisfy s1 < s2 < track_length
    use_cache : required. True memoizes the last hit, which helps a single car moving
        along the track and hurts random access (e.g. looking up many cars).
    schema_version : 1 when absent, 2 for files carrying the fields below
    speed_trap_m, drs_zones, overtake_zones, active_aero_zones : optional; every lap
        distance in them, and in brake boards, satisfies 0 <= value < track_length.
        Zones may cross the start line (end_m < start_m); segments may not.
    """

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    circuit_name: str
    circuit_number: int
    track_length: float = Field(gt=0)
    segments: Tuple[SegmentInfo, ...]
    sectors: SectorBoundaries
    use_cache: bool

    schema_version: Literal[1, 2] = 1
    speed_trap_m: Optional[float] = None
    drs_zones: Tuple[DrsZoneInfo, ...] = ()
    overtake_zones: Tuple[OvertakeZoneInfo, ...] = ()
    active_aero_zones: Tuple[ActiveAeroZoneInfo, ...] = ()

    # Public field for read speed (PrivateAttr reads are far slower); a dataclass so cache writes skip pydantic's __setattr__.
    # Safe because the class is internal: input data never reaches it.
    cache: CacheState = Field(default_factory=CacheState, exclude=True)

    @model_validator(mode="after")
    def _check_sectors_within_track(self) -> "TrackSegmentsClassifier":
        if self.sectors.s2 >= self.track_length:
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

    @model_validator(mode="after")
    def _check_zone_ids(self) -> "TrackSegmentsClassifier":
        for kind, zones in (("drs_zones", self.drs_zones), ("overtake_zones", self.overtake_zones)):
            ids = [z.id for z in zones]
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            if dupes:
                raise ValueError(f"{kind}: duplicate id {', '.join(str(i) for i in dupes)}")
        return self

    @model_validator(mode="after")
    def _check_lap_positions(self) -> "TrackSegmentsClassifier":
        for label, value in self._lap_positions():
            if not 0 <= value < self.track_length:
                raise ValueError(f"{label} ({value}) must be in [0, track_length={self.track_length})")
        return self

    def _lap_positions(self) -> Iterator[Tuple[str, float]]:
        """Every schema v2 lap distance, labelled for error messages."""
        if self.speed_trap_m is not None:
            yield "speed_trap_m", self.speed_trap_m
        for z in self.drs_zones:
            yield f"drs zone {z.id} detection_m", z.detection_m
            for a in z.activation:
                yield f"drs zone {z.id} activation start_m", a.start_m
                yield f"drs zone {z.id} activation end_m", a.end_m
        for z in self.overtake_zones:
            yield f"overtake zone {z.id} detection_m", z.detection_m
            yield f"overtake zone {z.id} activation_m", z.activation_m
        for i, z in enumerate(self.active_aero_zones):
            yield f"active aero zone {i} start_m", z.start_m
            yield f"active aero zone {i} end_m", z.end_m
        for seg in self.segments:
            if isinstance(seg, CornerSegmentInfo):
                for b in seg.brake_boards:
                    yield f"corner {seg.corner_number} {b.distance_m}m board at_m", b.at_m
            elif isinstance(seg, ComplexCornerSegmentInfo):
                for sub in seg.corners:
                    for b in sub.brake_boards:
                        yield f"corner {sub.corner_number} {b.distance_m}m board at_m", b.at_m

    # Field validator rather than post-init: the model is frozen, so segments can't be reassigned afterwards.
    # segment_id is the segment's index in the array.
    @field_validator("segments", mode="after")
    @classmethod
    def _stamp_segment_ids(cls, segments: Tuple[SegmentInfo, ...]) -> Tuple[SegmentInfo, ...]:
        return tuple(seg.model_copy(update={"segment_id": idx}) for idx, seg in enumerate(segments))

    @cached_property
    def starts(self) -> Tuple[float, ...]:
        """Segment start_m values, parallel to `segments`, for bisect."""
        return tuple(seg.start_m for seg in self.segments)

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

    def get_sector(self, lap_distance: float) -> LapData.Sector:
        """Return the sector containing the given lap position."""
        s = self.sectors
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

    def to_file_dict(self) -> Dict[str, Any]:
        """The track as it is written to a JSON file, in the files' key order.

        Loading a shipped file and dumping it gives the same data. A v1 track gets no v2 keys; a v2 track
        always gets its three zone lists, even when empty (Monaco has no active aero).
        """
        out: Dict[str, Any] = {}
        if self.schema_version == 2:
            out["schema_version"] = 2
        out |= {"circuit_name": self.circuit_name, "circuit_number": self.circuit_number,
                "track_length": _num(self.track_length)}
        if self.schema_version == 2:
            if self.speed_trap_m is not None:
                out["speed_trap_m"] = _num(self.speed_trap_m)
            out["drs_zones"] = [z.to_file_dict() for z in self.drs_zones]
            out["overtake_zones"] = [z.to_file_dict() for z in self.overtake_zones]
            out["active_aero_zones"] = [z.to_file_dict() for z in self.active_aero_zones]
        out["segments"] = [s.to_file_dict() for s in self.segments]
        out["sectors"] = {"s1": self.sectors.s1, "s2": self.sectors.s2}
        return out
