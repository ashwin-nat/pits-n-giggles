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

from pydantic import BaseModel, Field, field_validator

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class LoggingSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : False,
    }

    log_file: str = Field(
        default="png.log",
        description="Path to the log file (relative only)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    log_file_size: int = Field(
        default=1_000_000,
        gt=0,
        description="Maximum size of the log file (bytes)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )

    # Pydantic v2 field validators receive the model class as 'cls' automatically.
    # Not a classmethod, so we disable the no-self-argument warning.
    @field_validator("log_file")
    def validate_log_file(cls, v: str) -> str: # pylint: disable=no-self-argument
        if not v or not v.strip():
            raise ValueError("Log file name cannot be empty")
        v = v.strip()
        if "/" in v or "\\" in v:
            raise ValueError("Only a file name in the current directory is allowed")
        return v

    class Config:
        str_strip_whitespace = True
