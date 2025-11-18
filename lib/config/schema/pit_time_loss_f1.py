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

from pydantic import BaseModel, Field, field_validator, model_validator

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PitTimeLossF1(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : False,
    }

    # Not adding field level metadata since whole section is hidden in UI
    Melbourne: float = Field(18.0)
    Shanghai: float = Field(22.0)
    Suzuka: float = Field(22.0)
    Sakhir: float = Field(23.0)
    Jeddah: float = Field(18.0)
    Miami: float = Field(19.0)
    Imola: float = Field(27.0)
    Monaco: float = Field(19.0)
    Catalunya: float = Field(21.0)
    Montreal: float = Field(16.0)
    Austria: float = Field(19.0)
    Austria_Reverse: float = Field(19.0)
    Silverstone: float = Field(28.0)
    Silverstone_Reverse: float = Field(28.0)
    Hungaroring: float = Field(20.0)
    Zandvoort: float = Field(18.0)
    Spa: float = Field(18.0)
    Zandvoort_Reverse: float = Field(18.0)
    Monza: float = Field(24.0)
    Baku: float = Field(18.0)
    Singapore: float = Field(26.0)
    Texas: float = Field(20.0)
    Mexico: float = Field(22.0)
    Brazil: float = Field(20.0)
    Las_Vegas: float = Field(20.0)
    Losail: float = Field(25.0)
    Abu_Dhabi: float = Field(19.0)
    Paul_Ricard: float = Field(None)
    Portimao: float = Field(None)
