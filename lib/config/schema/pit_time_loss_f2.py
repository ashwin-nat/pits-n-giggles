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

class PitTimeLossF2(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    # Not adding field level metadata since whole section is hidden in UI
    Melbourne: Optional[float] = Field(None)
    Shanghai: Optional[float] = Field(None)
    Suzuka: Optional[float] = Field(None)
    Sakhir: Optional[float] = Field(None)
    Jeddah: Optional[float] = Field(None)
    Miami: Optional[float] = Field(None)
    Imola: Optional[float] = Field(None)
    Monaco: Optional[float] = Field(None)
    Catalunya: Optional[float] = Field(None)
    Montreal: Optional[float] = Field(None)
    Austria: Optional[float] = Field(None)
    Austria_Reverse: Optional[float] = Field(None)
    Silverstone: Optional[float] = Field(None)
    Silverstone_Reverse: Optional[float] = Field(None)
    Hungaroring: Optional[float] = Field(None)
    Zandvoort: Optional[float] = Field(None)
    Spa: Optional[float] = Field(None)
    Zandvoort_Reverse: Optional[float] = Field(None)
    Monza: Optional[float] = Field(None)
    Baku: Optional[float] = Field(None)
    Singapore: Optional[float] = Field(None)
    Texas: Optional[float] = Field(None)
    Mexico: Optional[float] = Field(None)
    Brazil: Optional[float] = Field(None)
    Las_Vegas: Optional[float] = Field(None)
    Losail: Optional[float] = Field(None)
    Abu_Dhabi: Optional[float] = Field(None)
    Paul_Ricard: Optional[float] = Field(None)
    Portimao: Optional[float] = Field(None)
