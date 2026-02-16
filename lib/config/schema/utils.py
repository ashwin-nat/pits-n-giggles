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

from enum import Enum
from typing import Optional, List

from pydantic import Field

# -------------------------------------- ENUM --------------------------------------------------------------------------

class PortType(Enum):
    TCP = "tcp"
    UDP = "udp"

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value: str):
        if value not in cls.__members__:
            return None
        return cls(value)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def udp_action_field(
        description: str,
        *,
        default: Optional[int] = None,
        visible: Optional[bool] = True,
        ext_info: Optional[List[str]] = None,
        group: Optional[str] = None):
    """
    Create a UDP action code field with standard bounds and schema extras.
    Only the description varies per leaf.
    """
    return Field(
        default=default,
        ge=1,
        le=12,
        validate_default=False,  # allow None
        strict=False,
        description=description,
        json_schema_extra={
            "ui": {
                "type": "text_box",
                "visible": visible,
                "ext_info": ext_info or [],
                "group": group,
            },
            "udp_action_code": True,
        },
    )

def ui_scale_field(description: str, *, default: Optional[float] = 1.0):
    """
    Create a UI scale field with standard bounds and schema extras.
    Only the description varies per leaf.
    """
    return Field(
        default=default,
        ge=0.5,
        le=2.0,
        description=description,
        json_schema_extra={
            "ui": {
                "type": "slider",
                "visible": False,
                "min_ui": 50,
                "max_ui": 200,
                "convert": "percent",
                "unit": "%"
            }
        },
    )

def overlay_enable_field(description: str, *, default: Optional[bool] = True, visible: Optional[bool] = True,
                         group: Optional[str] = None, ext_info: Optional[List[str]] = None):
    """
    Create an overlay enable field with standard schema extras.
    Only the description varies per leaf.
    """
    return Field(
        default=default,
        description=description,
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": visible,
                "overlay_enable": True,
                "group": group,
                "ext_info": ext_info or []
            }
        }
    )

def port_field(description: str, default: int, visible: Optional[bool] = True, port_type: PortType = PortType.TCP):
    """
    Create a port field with standard bounds and schema extras.
    Only the description varies per leaf.
    """
    return Field(
        default=default,
        gt=0,
        le=65535,
        description=description,
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": visible
            },
            "port_type": str(port_type)
        }
    )
