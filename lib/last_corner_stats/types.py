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
from typing import Union

from lib.track_segments_classifier.types import (ComplexCornerSegmentInfo,
                                                  CornerSegmentInfo)

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One high-frequency telemetry sample fed into LastCornerTracker.update()."""
    circuit_pos_m: float
    speed_kmph: int


@dataclass(frozen=True, slots=True)
class LastCornerStats:
    """Statistics for the most recently completed corner."""
    segment: Union[CornerSegmentInfo, ComplexCornerSegmentInfo]
    min_speed_kmph: int
