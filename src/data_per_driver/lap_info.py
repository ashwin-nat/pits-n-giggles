# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

from lib.f1_types import LapHistoryData, VisualTyreCompound
from typing import Optional
from dataclasses import dataclass
from src.png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass
class LapInfo:
    m_best_lap_ms: Optional[int] = None
    m_best_lap_obj: Optional[LapHistoryData] = None
    m_best_lap_tyre: Optional[VisualTyreCompound] = None
    m_pb_s1_ms: Optional[int] = None
    m_pb_s2_ms: Optional[int] = None
    m_pb_s3_ms: Optional[int] = None
    m_last_lap_ms: Optional[int] = None
    m_last_lap_obj: Optional[LapHistoryData] = None