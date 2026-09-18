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

from dataclasses import dataclass
from typing import Optional, Union

from lib.track_segments_classifier.types import (ComplexCornerSegmentInfo,
                                                  CornerSegmentInfo)

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One high-frequency telemetry sample fed into LastCornerTracker.update()."""
    circuit_num: int
    circuit_pos_m: float
    speed_kmph: int


@dataclass(frozen=True, slots=True)
class LastCornerStats:
    """Statistics for the most recently completed corner."""
    segment: Union[CornerSegmentInfo, ComplexCornerSegmentInfo]
    min_speed_kmph: int

    def to_dict(self) -> dict:
        """Convert to a JSON-serializable dict."""
        segment_dict = self.segment.to_dict()
        segment_dict["segment_id"] = self.segment.segment_id
        return {
            "segment": segment_dict,
            "min_speed_kmph": self.min_speed_kmph,
        }


@dataclass(frozen=True, slots=True)
class LastCornerStatsSnapshot:
    """LastCornerTracker.stats() return value.

    last_pub_data is the most recently completed corner's stats and is kept
    around across a new corner starting to accumulate - it is only cleared by
    reset(). is_accumulating tells the consumer whether a corner is currently
    being driven (there is no complete data for it yet), independent of
    whether last_pub_data happens to be populated.
    """
    is_accumulating: bool
    last_pub_data: Optional[LastCornerStats]

    def to_dict(self) -> dict:
        """Convert to a JSON-serializable dict."""
        return {
            "is_accumulating": self.is_accumulating,
            "last_pub_data": self.last_pub_data.to_dict() if self.last_pub_data else None,
        }
