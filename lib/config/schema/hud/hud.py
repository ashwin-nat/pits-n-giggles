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

import copy
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from ..diff import ConfigDiffMixin
from ..utils import overlay_enable_field, udp_action_field, ui_scale_field
from .layout import DEFAULT_OVERLAY_LAYOUT, OverlayPosition
from .mfd import MfdSettings

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class HudSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    enabled: bool = Field(
        default=False,
        description="Enable Overlays (only on Windows, setting will be ignored on other OS's)",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info": [
                    'Recommended to also configure "Toggle all overlays UDP action code" and \n'
                        '"Cycle MFD pages UDP action code" as well.'
                ]
            }
        }
    )

    show_lap_timer: bool = overlay_enable_field(description="Enable lap timer overlay")
    lap_timer_ui_scale: float = ui_scale_field(description="Lap Timer UI scale")
    lap_timer_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle lap timer overlay UDP action code")


    show_timing_tower: bool = overlay_enable_field(description="Enable timing tower overlay")
    timing_tower_ui_scale: float = ui_scale_field(description="Timing tower UI scale")
    timing_tower_max_rows: int = Field(
        default=5,
        ge=1,
        le=22,
        description="Max number of rows to show in timing tower (must be odd number or 22)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True
            }
        }
    )
    timing_tower_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle timing tower overlay UDP action code")

    show_mfd: bool = overlay_enable_field(description="Enable MFD overlay")
    mfd_ui_scale: float = ui_scale_field(description="MFD UI scale")
    mfd_settings: MfdSettings = Field(
        default=MfdSettings(),
        description="MFD overlay settings",
        json_schema_extra={
            "ui": {
                "type" : "reorderable_view",
                "visible": True
            }
        }
    )
    mfd_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle MFD overlay UDP action code")

    show_track_map: bool = overlay_enable_field(description="Enable track map overlay", default=False, visible=False)
    track_map_ui_scale: float = ui_scale_field(description="Track map UI scale")
    track_map_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle track map overlay UDP action code", visible=False)

    show_input_overlay: bool = overlay_enable_field(description="Enable input telemetry overlay")
    input_overlay_ui_scale: float = ui_scale_field(description="Input telemetry overlay UI scale")
    input_overlay_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle input telemetry overlay UDP action code")
    input_overlay_buffer_duration_sec: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Input telemetry overlay buffer duration (sec)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True,
                "ext_info": [
                    "Controls how much recent throttle, brake, and steering input history is shown in the overlay. "
                    "Higher values show a longer time window, while lower values make input changes appear more responsive.\n"
                    "Test out different values in heavy braking zones. Set a value where you can see the braking shape once you've exited the corner.\n"
                    "Recommendation: Bahrain T1"
                ]
            }
        }
    )

    show_track_radar_overlay: bool = overlay_enable_field(description="Enable track radar overlay")
    track_radar_overlay_ui_scale: float = ui_scale_field(description="Track radar overlay UI scale")
    track_radar_overlay_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle track radar overlay UDP action code")

    toggle_overlays_udp_action_code: Optional[int] = udp_action_field(
        "Toggle all overlays UDP action code")
    cycle_mfd_udp_action_code: Optional[int] = udp_action_field(
        "Cycle MFD pages UDP action code")

    overlays_opacity: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Overlays opacity percentage",
        json_schema_extra={
            "ui": {
                "type" : "slider",
                "visible": False,
                "min": 0,
                "max": 100
            }
        }
    )

    use_windowed_overlays: bool = Field(
        default=False,
        description="Use Windowed Overlays (Required for OBS window capture)",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )

    layout: Dict[str, OverlayPosition] = Field(
        default_factory=lambda: copy.deepcopy(DEFAULT_OVERLAY_LAYOUT),
        description="Overlay screen positions (pixels)",
        json_schema_extra={
            "ui": {
                "visible": False
            }
        }
    )

    def model_post_init(self, __context: Any) -> None: # pylint: disable=arguments-differ
        """Validate file existence only if HTTPS is enabled."""
        # Not allowed to enable HUD while all overlays are disabled
        if not self.enabled:
            return

        if not any(
            getattr(self, field_name)
            for field_name, field in type(self).model_fields.items()
            if field.json_schema_extra.get("ui", {}).get("overlay_enable", False)
        ):
            raise ValueError("HUD cannot be enabled while all overlays are disabled")

        if self.show_mfd and not self.mfd_settings.sorted_enabled_pages():
            raise ValueError("HUD cannot be enabled while all MFD pages are disabled")

    @field_validator("timing_tower_max_rows")
    def must_be_odd(cls, v): # pylint: disable=no-self-argument
        if (v != 22) and ((v % 2) == 0):
            raise ValueError("Timing tower max rows must be an odd number")
        return v

    @property
    def timing_tower_num_adjacent_cars(self) -> int:
        # Max rows already validated to be odd
        if self.timing_tower_max_rows == 22:
            return 11
        return (self.timing_tower_max_rows - 1) // 2

    @classmethod
    def get_layout_dict_from_json(cls, json_dict: Dict[str, int]) -> Dict[str, OverlayPosition]:
        return {k: OverlayPosition.fromJSON(v) for k, v in json_dict.items()}

    @property
    def layout_config_json(self) -> Dict[str, Dict[str, int]]:
        return {k: v.toJSON() for k, v in self.layout.items()}

    @classmethod
    def get_default_layout_json(cls) -> Dict[str, OverlayPosition]:
        return {k: v.toJSON() for k, v in DEFAULT_OVERLAY_LAYOUT.items()}

    @classmethod
    def get_default_layout_dict(cls) -> Dict[str, OverlayPosition]:
        return DEFAULT_OVERLAY_LAYOUT
