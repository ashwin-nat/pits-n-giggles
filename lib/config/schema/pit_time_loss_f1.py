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

from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PitTimeLossF1(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    # Not adding field level metadata since whole section is hidden in UI
    Melbourne: Optional[float] = Field(18.0)
    Shanghai: Optional[float] = Field(22.0)
    Suzuka: Optional[float] = Field(22.0)
    Sakhir: Optional[float] = Field(23.0)
    Jeddah: Optional[float] = Field(18.0)
    Miami: Optional[float] = Field(19.0)
    Imola: Optional[float] = Field(27.0)
    Monaco: Optional[float] = Field(19.0)
    Catalunya: Optional[float] = Field(21.0)
    Montreal: Optional[float] = Field(16.0)
    Austria: Optional[float] = Field(19.0)
    Austria_Reverse: Optional[float] = Field(19.0)
    Silverstone: Optional[float] = Field(28.0)
    Hungaroring: Optional[float] = Field(20.0)
    Zandvoort: Optional[float] = Field(18.0)
    Spa: Optional[float] = Field(18.0)
    Zandvoort_Reverse: Optional[float] = Field(18.0)
    Monza: Optional[float] = Field(24.0)
    Baku: Optional[float] = Field(18.0)
    Singapore: Optional[float] = Field(26.0)
    Texas: Optional[float] = Field(20.0)
    Mexico: Optional[float] = Field(22.0)
    Brazil: Optional[float] = Field(20.0)
    Las_Vegas: Optional[float] = Field(20.0)
    Losail: Optional[float] = Field(25.0)
    Abu_Dhabi: Optional[float] = Field(19.0)
    Paul_Ricard: Optional[float] = Field(None)
    Portimao: Optional[float] = Field(None)
