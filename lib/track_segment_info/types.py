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

from typing import Annotated, ClassVar, Dict, List, Literal, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

class BaseSegmentInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str
    name: str
    start_m: float
    end_m: float

    @model_validator(mode="after")
    def _check_range(self) -> "BaseSegmentInfo":
        if self.start_m >= self.end_m:
            raise ValueError(f"start_m ({self.start_m}) must be less than end_m ({self.end_m})")
        return self

    def render(self) -> Dict[str, str]:
        raise NotImplementedError


class StraightSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "straight"
    type: Literal["straight"] = "straight"

    @field_validator("name")
    @classmethod
    def _name_required(cls, v: str) -> str:
        if not v:
            raise ValueError("name is required for straight segments")
        return v

    def render(self) -> Dict[str, str]:
        return {"type": "straight", "name": self.name, "turns": ""}


class CornerSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "corner"
    type: Literal["corner"] = "corner"
    name: str = ""
    corner_number: int

    def render(self) -> Dict[str, str]:
        turns = f"Turn {self.corner_number}" if not self.name else f"T{self.corner_number}"
        return {"type": "corner", "name": self.name, "turns": turns}


class ComplexCornerSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "complex_corner"
    type: Literal["complex_corner"] = "complex_corner"
    name: str = ""
    corner_numbers: Tuple[int, ...]

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

    def render(self) -> Dict[str, str]:
        first, last = self.corner_numbers[0], self.corner_numbers[-1]
        if not self.name:
            turns = f"Turns {first}-{last}" if len(self.corner_numbers) > 2 else " / ".join(f"Turn {n}" for n in self.corner_numbers)
        else:
            turns = f"T{first}-T{last}" if len(self.corner_numbers) > 2 else " / ".join(f"T{n}" for n in self.corner_numbers)
        return {"type": "corner", "name": self.name, "turns": turns}


SegmentInfo = Annotated[
    Union[StraightSegmentInfo, CornerSegmentInfo, ComplexCornerSegmentInfo],
    Field(discriminator="type")
]


class TrackData(BaseModel):
    circuit_name: str
    circuit_number: int
    segments: List[SegmentInfo]

    @field_validator("segments", mode="after")
    @classmethod
    def _check_order_and_overlap(cls, segments: list) -> list:
        for i in range(1, len(segments)):
            prev, curr = segments[i - 1], segments[i]
            if curr.start_m < prev.start_m:
                raise ValueError(
                    f"segment {i} is out of order: start_m={curr.start_m} < previous start_m={prev.start_m}"
                )
            if curr.start_m < prev.end_m:
                raise ValueError(
                    f"segment {i} overlaps previous: start_m={curr.start_m} < previous end_m={prev.end_m}"
                )
        return segments
