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

import os
import re
from typing import ClassVar, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .file_path_str import FilePathStr

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class NetworkSettings(BaseModel):
    telemetry_port: int = Field(20777, ge=0, le=65535, description="F1 UDP Telemetry Port")
    server_port: int = Field(4768, ge=0, le=65535, description="Pits n' Giggles HTTP Server Port")
    save_viewer_port: int = Field(4769, ge=0, le=65535, description="Pits n' Giggles Save Data Viewer Port")
    udp_tyre_delta_action_code: int = Field(11, ge=1, le=12, description="Tyre Delta Marker: UDP Action Code")
    udp_custom_action_code: int = Field(12, ge=1, le=12, description="Custom Marker: UDP Action Code")

    @model_validator(mode="after")
    def check_ports_and_action_codes(self) -> "NetworkSettings":
        fields_map = type(self).model_fields

        if self.server_port == self.save_viewer_port:
            desc1 = fields_map["server_port"].description
            desc2 = fields_map["save_viewer_port"].description
            raise ValueError(f"{desc1} and {desc2} must not be the same (both are {self.server_port})")

        if self.udp_tyre_delta_action_code == self.udp_custom_action_code:
            desc1 = fields_map["udp_tyre_delta_action_code"].description
            desc2 = fields_map["udp_custom_action_code"].description
            raise ValueError(f"{desc1} and {desc2} must not be the same (both are {self.udp_tyre_delta_action_code})")

        return self

class CaptureSettings(BaseModel):
    post_race_data_autosave: bool = Field(True, description="Autosave race data at the end of races")
    post_quali_data_autosave: bool = Field(True,
                                           description="Autosave qualifying data at the end of qualifying sessions")
    post_fp_data_autosave: bool = Field(False,
                                        description="Autosave free practice data at the end of free practice sessions")

class DisplaySettings(BaseModel):
    refresh_interval: int = Field(200, gt=0, description="Pits n' Giggles client update interval (ms)")
    disable_browser_autoload: bool = Field(False, description="Disable automatic opening of the web page in the browser")

class LoggingSettings(BaseModel):
    log_file: str = Field("png.log", description="Path to the log file (relative only)")
    log_file_size: int = Field(1_000_000, gt=0, description="Maximum size of the log file (bytes)")

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

class PrivacySettings(BaseModel):
    process_car_setup: bool = Field(False, description="Whether to process car setup data")

class StreamOverlaySettings(BaseModel):
    show_sample_data_at_start: bool = Field(False, description="Show sample data until first real data arrives")

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

    # Pydantic v2 field validators receive the model class as 'cls' automatically.
    # Not a classmethod, so we disable the no-self-argument warning.
    @field_validator('target_1', 'target_2', 'target_3', mode='before')
    def validate_hostport(cls, val): # pylint: disable=no-self-argument
        if val is None:
            return ""
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

class HttpsSettings(BaseModel):
    enabled: bool = Field(False, description="Enable HTTPS support")
    key_file_path: FilePathStr = Field("", description="Path to SSL private key file")
    cert_file_path: FilePathStr = Field("", description="Path to SSL certificate file")

    def model_post_init(self, __context) -> None:
        """Validate file existence only if HTTPS is enabled."""
        if self.enabled:
            if not self.key_file_path.strip() or not os.path.isfile(self.key_file_path):
                raise ValueError("Key file is required and must exist when HTTPS is enabled")
            if not self.cert_file_path.strip() or not os.path.isfile(self.cert_file_path):
                raise ValueError("Certificate file is required and must exist when HTTPS is enabled")

    @property
    def proto(self) -> str:
        return "https" if self.enabled else "http"

class PngSettings(BaseModel):
    Network: NetworkSettings = Field(default_factory=NetworkSettings)
    Capture: CaptureSettings = Field(default_factory=CaptureSettings)
    Display: DisplaySettings = Field(default_factory=DisplaySettings)
    Logging: LoggingSettings = Field(default_factory=LoggingSettings)
    Privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    Forwarding: ForwardingSettings = Field(default_factory=ForwardingSettings)
    StreamOverlay: StreamOverlaySettings = Field(default_factory=StreamOverlaySettings)
    HTTPS: HttpsSettings = Field(default_factory=HttpsSettings)

    class Config:
        str_strip_whitespace = True

    def __str__(self) -> str:
        lines = ["PngSettings:"]
        for section_name, section_model in self:
            lines.append(f"  [{section_name}]")
            lines.extend(
                f"    {field_name} = {value}"
                for field_name, value in section_model
            )
        return "\n".join(lines)
