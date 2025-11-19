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

import re
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class ForwardingSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    target_1: Optional[str] = Field(
        default="",
        description="Target 1 (host:port)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    target_2: Optional[str] = Field(
        default="",
        description="Target 2 (host:port)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    target_3: Optional[str] = Field(
        default="",
        description="Target 3 (host:port)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )

    hostport_pattern: ClassVar[re.Pattern] = re.compile(
        r"""
        ^                             # Start of string
        ([a-zA-Z0-9.-]+)              # Hostname or IP
        :
        ([0-9]{1,5})                  # Port number
        $                             # End of string
        """,
        re.VERBOSE,
    )

    # Pydantic v2 field validators receive the model class as 'cls' automatically.
    # Not a classmethod, so we disable the no-self-argument warning.
    @field_validator('target_1', 'target_2', 'target_3', mode='before')
    def validate_hostport(cls, val): # pylint: disable=no-self-argument
        if val is None:
            return ""
        if not isinstance(val, str):
            raise ValueError(f"Invalid host:port format: '{val}'")
        v = val.strip()
        if not v:
            return v  # allow empty string
        match = cls.hostport_pattern.match(v)
        if not match:
            raise ValueError(f"Invalid host:port format: '{v}'")
        port = int(match.group(2))
        if port < 1 or port > 65535:
            raise ValueError(f"Port number out of range in '{v}'")
        return v

    @property
    def forwarding_targets(self) -> list[tuple[str, int]]:
        ret = []
        if self.target_1:
            ret.append((self._parse_hostport(self.target_1)))
        if self.target_2:
            ret.append((self._parse_hostport(self.target_2)))
        if self.target_3:
            ret.append((self._parse_hostport(self.target_3)))
        return ret

    def _parse_hostport(self, value: str) -> tuple[str, int]:
        """
        Parse a host:port string into (host, port) tuple.

        Raises:
            ValueError: if format is invalid or port is out of range.
        """
        host, port_str = value.strip().split(":")
        return host, int(port_str)
