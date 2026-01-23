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

from pydantic import BaseModel, Field

from ..diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class TimingTowerColOptions(BaseModel, ConfigDiffMixin):
    show_team_logos: bool = Field(
        default=True,
        description="Show team logos",
        json_schema_extra={"ui": {"type": "check_box"}}
    )

    show_tyre_info: bool = Field(
        default=True,
        description="Show tyre compound and wear information",
        json_schema_extra={"ui": {"type": "check_box"}}
    )

    show_deltas: bool = Field(
        default=True,
        description="Show time deltas",
        json_schema_extra={"ui": {"type": "check_box"}}
    )

    show_ers_drs_info: bool = Field(
        default=True,
        description="Show ERS / DRS status",
        json_schema_extra={"ui": {"type": "check_box"}}
    )

    show_pens: bool = Field(
        default=True,
        description="Show penalties",
        json_schema_extra={"ui": {"type": "check_box"}}
    )

    show_tl_warns: bool = Field(
        default=True,
        description="Show Track Limit warnings",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "ext_info": [
                    'Display track limit warns if the driver has no penalties instead of a blank cell'
                ]
            }
        }
    )
