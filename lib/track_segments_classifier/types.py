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

from typing import Annotated, Any, ClassVar, Dict, Literal, Tuple, Union

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

class SectorBoundaries(BaseModel):
    model_config = ConfigDict(frozen=True)

    s1: int
    s2: int

    @model_validator(mode="after")
    def _check_increasing(self) -> "SectorBoundaries":
        if self.s1 <= 0:
            raise ValueError(f"s1 must be greater than 0, got {self.s1}")
        if not (self.s1 < self.s2):
            raise ValueError(f"sector boundaries must be strictly increasing: s1={self.s1}, s2={self.s2}")
        return self


class BrakeBoardInfo(BaseModel):
    """A brake board: its label, its real lap distance, and which side of the track it stands on."""
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    distance_m: Literal[50, 100, 150, 200, 250, 300]
    at_m: float
    side: Literal["left", "right", "both"]


class SubCornerInfo(BaseModel):
    """One corner's part of a complex corner."""
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    corner_number: int
    name: str = ""
    start_m: float
    end_m: float
    brake_boards: Tuple[BrakeBoardInfo, ...] = ()

    @model_validator(mode="after")
    def _check_range(self) -> "SubCornerInfo":
        if self.start_m >= self.end_m:
            raise ValueError(
                f"corner {self.corner_number}: start_m ({self.start_m}) must be less than end_m ({self.end_m})"
            )
        return self


class LapRangeInfo(BaseModel):
    """A lap range that may cross the start line, shown by end_m < start_m."""
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    start_m: float
    end_m: float

    @model_validator(mode="after")
    def _check_not_empty(self) -> "LapRangeInfo":
        if self.start_m == self.end_m:
            raise ValueError(f"zone is empty: start_m equals end_m ({self.start_m})")
        return self


class DrsActivationInfo(LapRangeInfo):
    """One DRS activation range."""


class DrsZoneInfo(BaseModel):
    """A DRS detection point and the activation ranges it opens."""
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    id: int
    detection_m: float
    activation: Tuple[DrsActivationInfo, ...] = Field(min_length=1)


class OvertakeZoneInfo(BaseModel):
    """An overtake mode detection point and its activation point."""
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    id: int
    detection_m: float
    activation_m: float


class ActiveAeroZoneInfo(LapRangeInfo):
    """An active aero zone. Named to avoid lib.f1_types.ActiveAeroZone."""
    mode: Literal["full", "partial"]


class BaseSegmentInfo(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    TYPE: ClassVar[str]
    type: str
    name: str
    start_m: float
    end_m: float
    segment_id: int = -1

    @model_validator(mode="after")
    def _check_range(self) -> "BaseSegmentInfo":
        if self.start_m >= self.end_m:
            raise ValueError(f"start_m ({self.start_m}) must be less than end_m ({self.end_m})")
        return self

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def contains(self, lap_distance: float) -> bool:
        return self.start_m <= lap_distance < self.end_m

class StraightSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "straight"
    type: Literal["straight"] = "straight"

    @field_validator("name")
    @classmethod
    def _name_required(cls, v: str) -> str:
        if not v:
            raise ValueError("name is required for straight segments")
        return v

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "straight",
            "name": self.name,
        }


class CornerSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "corner"
    type: Literal["corner"] = "corner"
    name: str = ""
    corner_number: int
    brake_boards: Tuple[BrakeBoardInfo, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "corner",
            "name": self.name,
            "corner_number": self.corner_number,
        }


class ComplexCornerSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "complex_corner"
    type: Literal["complex_corner"] = "complex_corner"
    name: str = ""
    corner_numbers: Tuple[int, ...]
    corners: Tuple[SubCornerInfo, ...] = ()

    @field_validator("corner_numbers")
    @classmethod
    def _check_continuous(cls, v: Tuple[int, ...]) -> Tuple[int, ...]:
        if len(v) < 2:
            raise ValueError("complex_corner must have at least 2 corner numbers")
        for i in range(1, len(v)):
            if v[i] != v[i - 1] + 1:
                raise ValueError(
                    f"corner_numbers must be strictly increasing and continuous, "
                    f"got {v[i - 1]} followed by {v[i]}"
                )
        return v

    @model_validator(mode="after")
    def _check_sub_corners(self) -> "ComplexCornerSegmentInfo":
        """When present, corners must match corner_numbers and tile the segment exactly."""
        if not self.corners:
            return self
        numbers = tuple(c.corner_number for c in self.corners)
        if numbers != self.corner_numbers:
            raise ValueError(
                f"{self._label()}: corners numbered {list(numbers)} must match "
                f"corner_numbers {list(self.corner_numbers)}"
            )
        if self.corners[0].start_m != self.start_m:
            raise ValueError(
                f"{self._label()}: corner {numbers[0]} starts at {self.corners[0].start_m}, "
                f"not at the segment start {self.start_m}"
            )
        if self.corners[-1].end_m != self.end_m:
            raise ValueError(
                f"{self._label()}: corner {numbers[-1]} ends at {self.corners[-1].end_m}, "
                f"not at the segment end {self.end_m}"
            )
        for prev, curr in zip(self.corners, self.corners[1:]):
            if curr.start_m != prev.end_m:
                raise ValueError(
                    f"{self._label()}: corner {curr.corner_number} starts at {curr.start_m}, "
                    f"not where corner {prev.corner_number} ends ({prev.end_m})"
                )
        return self

    def _label(self) -> str:
        return f"complex_corner {self.name!r} at {self.start_m}m" if self.name else f"complex_corner at {self.start_m}m"

    def to_dict(self) -> Dict[str, object]:
        return {
            "type": "complex_corner",
            "name": self.name,
            "corner_numbers": list(self.corner_numbers),
        }


SegmentInfo = Annotated[
    Union[StraightSegmentInfo, CornerSegmentInfo, ComplexCornerSegmentInfo],
    Field(discriminator="type")
]
