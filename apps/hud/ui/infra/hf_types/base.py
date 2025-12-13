# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HighFreqBase:
    __hf_type__: str

    def __init_subclass__(cls, **kwargs):
        cls.__hf_type__ = cls.__name__

@dataclass
class InputTelemetryData(HighFreqBase):
    throttle: float
    brake: float
    steering: float
    rev_pct: float

    @classmethod
    def from_json(cls, data: dict) -> "InputTelemetryData":
        return cls(
            throttle=float(data.get("throttle", 0.0)),
            brake=float(data.get("brake", 0.0)),
            steering=float(data.get("steering", 0.0)),
            rev_pct=float(data.get("rev_pct", 0.0)),
        )