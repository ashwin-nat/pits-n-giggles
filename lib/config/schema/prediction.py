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

class PredictionSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible": True,
    }

    weather_aware_prediction: bool = Field(
        default=False,
        description="Enable weather-aware tyre wear prediction",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
                "ext_info": [
                    "EXPERIMENTAL: When enabled, tyre wear regression uses only laps from the "
                    "current weather group (dry or wet), ignoring earlier laps recorded under "
                    "different conditions. This improves accuracy after weather transitions but "
                    "may produce unstable predictions early in a new weather segment."
                ]
            }
        }
    )

    tyre_wear_window_size: Optional[int] = Field(
        default=None,
        ge=2,
        description="Sliding window size for tyre wear prediction (laps)",
        json_schema_extra={
            "ui": {
                "type": "text_box",
                "visible": True,
                "ext_info": [
                    "EXPERIMENTAL: Limits tyre wear regression to the N most recent racing laps. "
                    "Helps the model adapt quickly to changing conditions (e.g. dry to wet) "
                    "instead of averaging over the entire stint. "
                    "Leave empty to use all available data (default behaviour)."
                ]
            }
        }
    )
