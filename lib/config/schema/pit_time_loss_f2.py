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

from typing import Any, ClassVar, Dict

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PitTimeLossF2(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : False,
    }

    # Not adding field level metadata since whole section is hidden in UI
    Melbourne: float = Field(None)
    Shanghai: float = Field(None)
    Suzuka: float = Field(None)
    Sakhir: float = Field(None)
    Jeddah: float = Field(None)
    Miami: float = Field(None)
    Imola: float = Field(None)
    Monaco: float = Field(None)
    Catalunya: float = Field(None)
    Montreal: float = Field(None)
    Austria: float = Field(None)
    Austria_Reverse: float = Field(None)
    Silverstone: float = Field(None)
    Silverstone_Reverse: float = Field(None)
    Hungaroring: float = Field(None)
    Zandvoort: float = Field(None)
    Spa: float = Field(None)
    Zandvoort_Reverse: float = Field(None)
    Monza: float = Field(None)
    Baku: float = Field(None)
    Singapore: float = Field(None)
    Texas: float = Field(None)
    Mexico: float = Field(None)
    Brazil: float = Field(None)
    Las_Vegas: float = Field(None)
    Losail: float = Field(None)
    Abu_Dhabi: float = Field(None)
    Paul_Ricard: float = Field(None)
    Portimao: float = Field(None)
