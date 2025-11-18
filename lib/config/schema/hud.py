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

class HudSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    enabled: bool = Field(
        default=False,
        description="Enable HUD (only on Windows, setting will be ignored on other OS's)",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    show_lap_timer: bool = Field(
        default=True,
        description="Show lap timer overlay",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    show_timing_tower: bool = Field(
        default=True,
        description="Show timing tower overlay",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    show_mfd: bool = Field(
        default=True,
        description="Show MFD overlay",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    toggle_overlays_udp_action_code: int = Field(
        default=10,
        ge=1,
        le=12,
        description="The UDP custom action code to show/hide overlays",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            },
            "udp_action_code" : True
        }
    )
    cycle_mfd_udp_action_code: int = Field(
        default=9,
        ge=1,
        le=12,
        description="The UDP custom action code to cycle MFD pages",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            },
            "udp_action_code" : True
        }
    )
    overlays_opacity: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Overlays opacity percentage",
        json_schema_extra={
            "ui": {
                "type" : "slider",
                "visible": True,
                "min": 0,
                "max": 100
            }
        }
    )

    def model_post_init(self, __context: Any) -> None: # pylint: disable=arguments-differ
        """Validate file existence only if HTTPS is enabled."""
        # Not allowed to enable HUD while all overlays are disabled
        if self.enabled:
            if not self.show_lap_timer and not self.show_timing_tower and not self.show_mfd:
                raise ValueError("HUD cannot be enabled while all overlays are disabled")
