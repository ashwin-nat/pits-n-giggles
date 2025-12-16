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

from pydantic import BaseModel, Field, model_validator

from .capture import CaptureSettings
from .diff import ConfigDiffMixin
from .display import DisplaySettings
from .forwarding import ForwardingSettings
from .https import HttpsSettings
from .hud import HudSettings
from .network import NetworkSettings
from .pit_time_loss_f1 import PitTimeLossF1
from .pit_time_loss_f2 import PitTimeLossF2
from .privacy import PrivacySettings
from .stream_overlay import StreamOverlaySettings
from .subsys_ctrl import SubSysCtrl

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PngSettings(ConfigDiffMixin, BaseModel):
    Network: NetworkSettings = Field(default_factory=NetworkSettings, description="Network")
    Capture: CaptureSettings = Field(default_factory=CaptureSettings, description="Save Data")
    Display: DisplaySettings = Field(default_factory=DisplaySettings, description="Display")
    Privacy: PrivacySettings = Field(default_factory=PrivacySettings, description="Privacy")
    Forwarding: ForwardingSettings = Field(default_factory=ForwardingSettings, description="UDP Forwarding")
    StreamOverlay: StreamOverlaySettings = Field(default_factory=StreamOverlaySettings, description="Stream Overlay")
    HTTPS: HttpsSettings = Field(default_factory=HttpsSettings, description="HTTPS")
    HUD: HudSettings = Field(default_factory=HudSettings, description="Overlays")
    TimeLossInPitsF1: PitTimeLossF1 = Field(default_factory=PitTimeLossF1, description="Pit Time Loss F1")
    TimeLossInPitsF2: PitTimeLossF2 = Field(default_factory=PitTimeLossF2, description="Pit Time Loss F2")
    SubSysCtrlCfg__: SubSysCtrl = Field(default_factory=SubSysCtrl, description="Subsys Control")
    class Config:
        str_strip_whitespace = True

    @model_validator(mode="after")
    def check_udp_action_codes(self) -> "PngSettings":
        """Ensure all configured (non-None) UDP action code fields across subsettings are unique."""
        udp_fields = []

        # Walk through submodels
        for section_name, section in self.__dict__.items():
            if isinstance(section, BaseModel):
                # Access model_fields via the class (Pydantic v2/v3 safe)
                for field_name, field in type(section).model_fields.items():
                    extra = field.json_schema_extra or {}
                    if extra.get("udp_action_code"):
                        value = getattr(section, field_name)
                        udp_fields.append((f"{section_name}.{field_name}", value))

        # Check for duplicates among configured (non-None) values
        seen = {}
        for name, val in udp_fields:
            if val is None:
                continue

            if val in seen:
                raise ValueError(
                    f"Duplicate UDP action code {val} between {seen[val]} and {name}"
                )
            seen[val] = name

        return self

    @model_validator(mode="after")
    def check_port_conflicts(self) -> "PngSettings":
        """Ensure all configured ports are unique per protocol (TCP / UDP)."""

        # port_type -> port_value -> "Section.field"
        ports_by_type: dict[str, dict[int, str]] = {}

        # Walk through submodels
        for section_name, section in self.__dict__.items():
            if not isinstance(section, BaseModel):
                continue

            for field_name, field in type(section).model_fields.items():
                extra = field.json_schema_extra or {}
                port_type = extra.get("port_type")

                # Not a port field
                if not port_type:
                    continue

                value = getattr(section, field_name)
                if value is None:
                    continue

                ports_by_type.setdefault(port_type, {})

                if value in ports_by_type[port_type]:
                    prev = ports_by_type[port_type][value]
                    raise ValueError(
                        f"Duplicate {port_type.upper()} port {value} between "
                        f"{prev} and {section_name}.{field_name}"
                    )

                ports_by_type[port_type][value] = f"{section_name}.{field_name}"

        return self

    def __str__(self) -> str:
        lines = ["PngSettings:"]
        for section_name, section_model in self:
            lines.append(f"  [{section_name}]")
            lines.extend(
                f"    {field_name} = {value}"
                for field_name, value in section_model
            )
        return "\n".join(lines)
