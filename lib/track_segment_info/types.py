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

from typing import Annotated, ClassVar, List, Literal, Tuple, Union

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


class StraightSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "straight"
    type: Literal["straight"] = "straight"


class CornerSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "corner"
    type: Literal["corner"] = "corner"
    corner_number: int


class ComplexCornerSegmentInfo(BaseSegmentInfo):
    TYPE: ClassVar[str] = "complex_corner"
    type: Literal["complex_corner"] = "complex_corner"
    corner_numbers: Tuple[int, ...]


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
