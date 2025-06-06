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
from typing import ClassVar, Optional

from pydantic import BaseModel, Field, field_validator

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class NetworkSettings(BaseModel):
    telemetry_port: int = Field(20777, ge=0, le=65535, description="F1 UDP Telemetry Port")
    server_port: int = Field(4768, ge=0, le=65535, description="Pits n' Giggles HTTP Server Port")
    save_viewer_port: int = Field(4769, ge=0, le=65535, description="Pits n' Giggles Save Data Viewer Port")
    udp_tyre_delta_action_code: int = Field(11, ge=1, le=12, description="Tyre Delta Marker: UDP Action Code")
    udp_custom_action_code: int = Field(12, ge=1, le=12, description="Custom Marker: UDP Action Code")

class CaptureSettings(BaseModel):
    post_race_data_autosave: bool = Field(False, description="Whether to autosave race data at the end of the race")

class DisplaySettings(BaseModel):
    refresh_interval: int = Field(200, gt=0, description="Pits n' Giggles client update interval (ms)")
    disable_browser_autoload: bool = Field(False, description="Disable automatic opening of the web page in the browser")

class LoggingSettings(BaseModel):
    log_file: str = Field("png.log", description="Path to the log file")
    log_file_size: int = Field(1_000_000, gt=0, description="Maximum size of the log file (bytes)")

class PrivacySettings(BaseModel):
    process_car_setup: bool = Field(False, description="Whether to process car setup data")

class ForwardingSettings(BaseModel):
    target_1: Optional[str] = ""
    target_2: Optional[str] = ""
    target_3: Optional[str] = ""

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

    @field_validator('target_1', 'target_2', 'target_3', mode='before')
    def validate_hostport(cls, val):
        v = val.rstrip()
        if not v:
            return v  # allow empty string
        match = cls.hostport_pattern.match(v)
        if not match:
            raise ValueError(f"Invalid host:port format: '{v}'")
        port = int(match.group(2))
        if port < 1 or port > 65535:
            raise ValueError(f"Port number out of range in '{v}'")
        return v

class PngSettings(BaseModel):
    Network: NetworkSettings
    Capture: CaptureSettings
    Display: DisplaySettings
    Logging: LoggingSettings
    Privacy: PrivacySettings
    Forwarding: ForwardingSettings

    class Config:
        str_strip_whitespace = True
