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
from typing import Any, ClassVar, Iterable, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from meta.meta import APP_NAME

from .file_path_str import FilePathStr

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class ConfigDiffMixin:
    """Provides recursive diffing and change detection for Pydantic config models."""

    def diff(self, other: "ConfigDiffMixin", fields: dict[str, list[str]] | list[str] | None = None) -> dict[str, Any]:
        """
        Return a nested dict showing changed fields and their old/new values.

        If `fields` is None, {}, or [], compares all model fields recursively.

        Example:
        {
            "Network": {
                "server_port": {"old_value": 4768, "new_value": 9999}
            }
        }
        """
        result: dict[str, Any] = {}

        # --- Case 1: Nested dict: {"Network": ["server_port", "udp_custom_action_code"]}
        if isinstance(fields, dict) and fields:
            for section, subfields in fields.items():
                self_section = getattr(self, section, None)
                other_section = getattr(other, section, None)
                if self_section is None or other_section is None:
                    continue

                if hasattr(self_section, "diff"):
                    section_diff = self_section.diff(other_section, subfields)
                else:
                    section_diff = self._basic_diff(self_section, other_section, subfields)

                if section_diff:
                    result[section] = section_diff
            return result

        # --- Case 2: Flat list of fields
        if isinstance(fields, list) and fields:
            return self._basic_diff(self, other, fields)

        # --- Case 3: fields is None, empty list, or empty dict → compare everything recursively
        result = {}
        for name, value in getattr(self, "__dict__", {}).items():
            other_value = getattr(other, name, None)
            if isinstance(value, ConfigDiffMixin) and isinstance(other_value, ConfigDiffMixin):
                subdiff = value.diff(other_value)
                if subdiff:
                    result[name] = subdiff
            else:
                if value != other_value:
                    result[name] = {"old_value": value, "new_value": other_value}
        return result

    def _basic_diff(self, self_obj: Any, other_obj: Any, fields: Iterable[str]) -> dict[str, Any]:
        """Compare plain attributes and return a dict of changed fields with old/new values."""
        changes = {}
        for f in fields:
            old_val = getattr(self_obj, f, None)
            new_val = getattr(other_obj, f, None)
            if old_val != new_val:
                changes[f] = {"old_value": old_val, "new_value": new_val}
        return changes

    def has_changed(self, other: "ConfigDiffMixin", fields: dict[str, list[str]] | list[str] | None = None) -> bool:
        """Return True if any watched field (or any field if none specified) differs."""
        return bool(self.diff(other, fields))

class NetworkSettings(ConfigDiffMixin, BaseModel):
    telemetry_port: int = Field(20777, ge=0, le=65535, description="F1 UDP Telemetry Port")
    server_port: int = Field(4768, ge=0, le=65535, description=f"{APP_NAME} HTTP Server Port")
    save_viewer_port: int = Field(4769, ge=0, le=65535, description=f"{APP_NAME} Save Data Viewer Port")
    udp_tyre_delta_action_code: int = Field(11, ge=1, le=12, description="Tyre Delta Marker: UDP Action Code")
    udp_custom_action_code: int = Field(12, ge=1, le=12, description="Custom Marker: UDP Action Code")
    wdt_interval_sec: int = Field(30, ge=1, le=120, description="UDP Telemetry Timeout (sec)")

    @model_validator(mode="after")
    def check_ports_and_action_codes(self) -> "NetworkSettings":
        fields_map = type(self).model_fields

        if self.server_port == self.save_viewer_port:
            desc1 = fields_map["server_port"].description # pylint: disable=unsubscriptable-object
            desc2 = fields_map["save_viewer_port"].description # pylint: disable=unsubscriptable-object
            raise ValueError(f"{desc1} and {desc2} must not be the same (both are {self.server_port})")

        if self.udp_tyre_delta_action_code == self.udp_custom_action_code:
            desc1 = fields_map["udp_tyre_delta_action_code"].description # pylint: disable=unsubscriptable-object
            desc2 = fields_map["udp_custom_action_code"].description # pylint: disable=unsubscriptable-object
            raise ValueError(f"{desc1} and {desc2} must not be the same (both are {self.udp_tyre_delta_action_code})")

        return self

class CaptureSettings(ConfigDiffMixin, BaseModel):
    post_race_data_autosave: bool = Field(True, description="Autosave race data at the end of races")
    post_quali_data_autosave: bool = Field(True,
                                           description="Autosave qualifying data at the end of qualifying sessions")
    post_fp_data_autosave: bool = Field(False,
                                        description="Autosave free practice data at the end of free practice sessions")
    post_tt_data_autosave: bool = Field(False,
                                        description="Autosave time trial data at the end of time trial sessions")
    save_race_ctrl_msg: bool = Field(False, description="Save race control messages")

class DisplaySettings(ConfigDiffMixin, BaseModel):
    refresh_interval: int = Field(200, gt=0, description=f"{APP_NAME} client update interval (ms)")
    disable_browser_autoload: bool = Field(False, description="Disable automatic opening of the web page in the browser")

class LoggingSettings(ConfigDiffMixin, BaseModel):
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

class PrivacySettings(ConfigDiffMixin, BaseModel):
    process_car_setup: bool = Field(False, description="Whether to process car setup data")

class StreamOverlaySettings(ConfigDiffMixin, BaseModel):
    show_sample_data_at_start: bool = Field(False, description="Show sample data until first real data arrives")
    stream_overlay_update_interval_ms: int = Field(100, ge=50,
                                                   description="Interval between data updates to the stream overlay (ms)")

class ForwardingSettings(ConfigDiffMixin, BaseModel):
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

class HttpsSettings(ConfigDiffMixin, BaseModel):
    enabled: bool = Field(False, description="Enable HTTPS support")
    key_file_path: FilePathStr = Field("", description="Path to SSL private key file")
    cert_file_path: FilePathStr = Field("", description="Path to SSL certificate file")

    def model_post_init(self, __context: Any) -> None: # pylint: disable=arguments-differ
        """Validate file existence only if HTTPS is enabled."""
        if self.enabled:
            if not self.key_file_path.strip() or not os.path.isfile(self.key_file_path): # pylint: disable=no-member
                raise ValueError("Key file is required and must exist when HTTPS is enabled")
            if not self.cert_file_path.strip() or not os.path.isfile(self.cert_file_path): # pylint: disable=no-member
                raise ValueError("Certificate file is required and must exist when HTTPS is enabled")

    @property
    def proto(self) -> str:
        return "https" if self.enabled else "http"

    @property
    def cert_path(self) -> Optional[str]:
        """Path to SSL certificate file. Will be None if HTTPS is disabled."""
        return None if not self.enabled else self.cert_file_path

    @property
    def key_path(self) -> Optional[str]:
        """Path to SSL private key file. Will be None if HTTPS is disabled."""
        return None if not self.enabled else self.key_file_path

class PitTimeLossF1(ConfigDiffMixin, BaseModel):
    Melbourne: float = Field(18.0)
    Shanghai: float = Field(22.0)
    Suzuka: float = Field(22.0)
    Sakhir: float = Field(23.0)
    Jeddah: float = Field(18.0)
    Miami: float = Field(19.0)
    Imola: float = Field(27.0)
    Monaco: float = Field(19.0)
    Catalunya: float = Field(21.0)
    Montreal: float = Field(16.0)
    Austria: float = Field(19.0)
    Austria_Reverse: float = Field(19.0)
    Silverstone: float = Field(28.0)
    Silverstone_Reverse: float = Field(28.0)
    Hungaroring: float = Field(20.0)
    Zandvoort: float = Field(18.0)
    Spa: float = Field(18.0)
    Zandvoort_Reverse: float = Field(18.0)
    Monza: float = Field(24.0)
    Baku: float = Field(18.0)
    Singapore: float = Field(26.0)
    Texas: float = Field(20.0)
    Mexico: float = Field(22.0)
    Brazil: float = Field(20.0)
    Las_Vegas: float = Field(20.0)
    Losail: float = Field(25.0)
    Abu_Dhabi: float = Field(19.0)
    Paul_Ricard: float = Field(None)
    Portimao: float = Field(None)

class PitTimeLossF2(ConfigDiffMixin, BaseModel):
    Melbourne: float = Field(None)
    Shanghai: float = Field(None)
    Suzuka: float = Field(None)
    Sakhir: float = Field(None)
    Jeddah: float = Field(None)
    Miami: float = Field(None)
    Imola: float = Field(None)
    Monaco: float = Field(None)
    Catalunya: float = Field(None)
    Montreal: float = Field(None)
    Austria: float = Field(None)
    Austria_Reverse: float = Field(None)
    Silverstone: float = Field(None)
    Silverstone_Reverse: float = Field(None)
    Hungaroring: float = Field(None)
    Zandvoort: float = Field(None)
    Spa: float = Field(None)
    Zandvoort_Reverse: float = Field(None)
    Monza: float = Field(None)
    Baku: float = Field(None)
    Singapore: float = Field(None)
    Texas: float = Field(None)
    Mexico: float = Field(None)
    Brazil: float = Field(None)
    Las_Vegas: float = Field(None)
    Losail: float = Field(None)
    Abu_Dhabi: float = Field(None)
    Paul_Ricard: float = Field(None)
    Portimao: float = Field(None)

class SubSysCtrl(ConfigDiffMixin, BaseModel):
    heartbeat_interval: float = Field(5.0, ge=1.0, le=60.0)
    num_missable_heartbeats: int = Field(3, ge=1, le=20)

class PngSettings(ConfigDiffMixin, BaseModel):
    Network: NetworkSettings = Field(default_factory=NetworkSettings)
    Capture: CaptureSettings = Field(default_factory=CaptureSettings)
    Display: DisplaySettings = Field(default_factory=DisplaySettings)
    Logging: LoggingSettings = Field(default_factory=LoggingSettings)
    Privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    Forwarding: ForwardingSettings = Field(default_factory=ForwardingSettings)
    StreamOverlay: StreamOverlaySettings = Field(default_factory=StreamOverlaySettings)
    HTTPS: HttpsSettings = Field(default_factory=HttpsSettings)
    TimeLossInPitsF1: PitTimeLossF1 = Field(default_factory=PitTimeLossF1)
    TimeLossInPitsF2: PitTimeLossF2 = Field(default_factory=PitTimeLossF2)
    SubSysCtrlCfg__: SubSysCtrl = Field(default_factory=SubSysCtrl)
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
