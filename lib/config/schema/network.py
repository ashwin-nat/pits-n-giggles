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

from pydantic import BaseModel, Field, model_validator

from meta.meta import APP_NAME

from .diff import ConfigDiffMixin
from .utils import PortType, port_field, udp_action_field

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class NetworkSettings(ConfigDiffMixin, BaseModel):

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }
    # TODO: migrate all to port_field
    telemetry_port: int = Field(
        default=20777,
        ge=0,
        le=65535,
        description="F1 UDP Telemetry Port",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    server_port: int = Field(
        default=4768,
        ge=0,
        le=65535,
        description=f"{APP_NAME} HTTP Server Port",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    save_viewer_port: int = Field(
        default=4769,
        ge=0,
        le=65535,
        description=f"{APP_NAME} Save Data Viewer Port",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    broker_xpub_port: int = port_field(
        "PitWall Downstream Port",
        default=53838,
        port_type=PortType.TCP,
    )

    broker_xsub_port: int = port_field(
        "PitWall Upstream Port",
        default=53835,
        port_type=PortType.TCP,
    )

    udp_tyre_delta_action_code: Optional[int] = udp_action_field("Tyre Delta Marker UDP Action Code")
    udp_custom_action_code: Optional[int] = udp_action_field("Custom Marker UDP Action Code")

    wdt_interval_sec: int = Field(
        default=30,
        ge=1,
        le=120,
        description="UDP Telemetry Timeout (sec)",
        json_schema_extra={
            "ui": {
                "type" : "text_box"
            }
        }
    )

    @model_validator(mode="after")
    def check_ports_and_action_codes(self) -> "NetworkSettings":
        # TODO: update to use annotations
        fields_map = type(self).model_fields

        if self.server_port == self.save_viewer_port:
            desc1 = fields_map["server_port"].description # pylint: disable=unsubscriptable-object
            desc2 = fields_map["save_viewer_port"].description # pylint: disable=unsubscriptable-object
            raise ValueError(f"{desc1} and {desc2} must not be the same (both are {self.server_port})")

        if (self.udp_custom_action_code and self.udp_tyre_delta_action_code) and \
                (self.udp_tyre_delta_action_code == self.udp_custom_action_code):
            desc1 = fields_map["udp_tyre_delta_action_code"].description # pylint: disable=unsubscriptable-object
            desc2 = fields_map["udp_custom_action_code"].description # pylint: disable=unsubscriptable-object
            raise ValueError(f"{desc1} and {desc2} must not be the same (both are {self.udp_tyre_delta_action_code})")

        return self
