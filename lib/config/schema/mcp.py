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

from collections import defaultdict
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, model_validator

from meta.meta import APP_NAME

from .diff import ConfigDiffMixin
from .utils import PortType, port_field, udp_action_field

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class McpSettings(ConfigDiffMixin, BaseModel):

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    mcp_http_server_enable: bool = Field(
        default=False,
        description="Enable MCP HTTP Server",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info": [
                    "Allows AI assistants (like ChatGPT) and other advanced tools to access "
                    "live race data from Pits n' Giggles."
                ]
            }
        }
    )

    mcp_http_port: int = port_field(
        "MCP HTTP Server Port",
        default=4770,
        port_type=PortType.TCP)
