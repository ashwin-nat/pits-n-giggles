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


class CaptureSettings(ConfigDiffMixin, BaseModel):

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    post_race_data_autosave: bool = Field(
        default=True,
        description="Autosave race data at the end of races",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    post_quali_data_autosave: bool = Field(
        default=True,
        description="Autosave qualifying data at the end of qualifying sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    post_fp_data_autosave: bool = Field(
        default=False,
        description="Autosave free practice data at the end of free practice sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    post_tt_data_autosave: bool = Field(
        default=False,
        description="Autosave time trial data at the end of time trial sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    save_race_ctrl_msg: bool = Field(
        default=False,
        description="Save race control messages",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
