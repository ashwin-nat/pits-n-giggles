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
from enum import Enum
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from ..diff import ConfigDiffMixin
from ..utils import overlay_enable_field, udp_action_field, ui_scale_field
from .layout import (DEFAULT_OVERLAY_LAYOUT, OverlayPosition,
                     merge_overlay_layout)
from .mfd import MfdSettings
from .timing_tower import TimingTowerColOptions

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class WeatherMFDUIType(str, Enum):
    CARDS = "Cards"
    GRAPH = "Graph"

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
    toggle_overlays_udp_action_code: Optional[int] = udp_action_field("Toggle all overlays UDP action code")
    use_windowed_overlays: bool = Field(
        default=False,
        description="Use Windowed Overlays (Required for OBS window capture)",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
            }
        }
    )

    # ============== LAP TIMER OVERLAY ==============
    show_lap_timer: bool = overlay_enable_field(description="Enable lap timer overlay", group="Lap Timer")
    lap_timer_ui_scale: float = ui_scale_field(description="Lap Timer UI scale")
    lap_timer_toggle_udp_action_code: Optional[int] = udp_action_field(description="Toggle lap timer overlay UDP action code",
                                                                        group="Lap Timer")

    # ============== TIMING TOWER OVERLAY ==============
    show_timing_tower: bool = overlay_enable_field(description="Enable timing tower overlay", group="Timing Tower")
    timing_tower_ui_scale: float = ui_scale_field(description="Timing tower UI scale")
    timing_tower_max_rows: int = Field(
        default=5,
        ge=1,
        le=22,
        description="Max number of rows to show in timing tower (must be odd number or 22)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True,
                "group": "Timing Tower"
            }
        }
    )
    timing_tower_col_options: TimingTowerColOptions = Field(
        default=TimingTowerColOptions(),
        description="Timing Tower Column Options",
        json_schema_extra={
            "ui": {
                "type" : "group_box",
                "visible": True,
                "group": "Timing Tower"
            }
        }
    )
    timing_tower_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle timing tower overlay UDP action code", group="Timing Tower")

    # ============== MFD OVERLAY ==============
    show_mfd: bool = overlay_enable_field(description="Enable MFD overlay", group="MFD")
    mfd_ui_scale: float = ui_scale_field(description="MFD UI scale")
    mfd_settings: MfdSettings = Field(
        default=MfdSettings(),
        description="MFD overlay settings",
        json_schema_extra={
            "ui": {
                "type" : "reorderable_view",
                "visible": True,
                "group": "MFD"
            }
        }
    )
    mfd_tyre_wear_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Tyre wear threshold for MFD (Tyre Wear Page)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True,
                "group": "MFD",
                "ext_info": [
                    "Used by the Tyre Wear page in the MFD to select the end lap.\n"
                    "The first lap exceeding this wear value is chosen; if none do, the final prediction lap is used."
                ],
            }
        }
    )
    mfd_weather_page_ui_type: WeatherMFDUIType = Field(
        default=WeatherMFDUIType.CARDS,
        description="MFD weather forecast page UI type",
        json_schema_extra={
            "ui": {
                "type": "radio_buttons",
                "options": [e.value for e in WeatherMFDUIType],
                "visible": True,
                "group": "MFD",
            }
        }
    )
    mfd_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle MFD overlay UDP action code", group="MFD")
    mfd_interaction_udp_action_code: Optional[int] = udp_action_field(
            description="Interact with active MFD page - UDP action code",
            ext_info=[
                "Optional action code to interact with currently active MFD page. Currently, "
                "the weather forecast page uses this to cycle through various sessions, if available. (only from F1 24+)"
            ],
            group="MFD",
        )
    cycle_mfd_udp_action_code: Optional[int] = udp_action_field(
        "Cycle MFD pages UDP action code", group="MFD")

    # ============== TRACK MAP OVERLAY ==============
    show_track_map: bool = overlay_enable_field(description="Enable track map overlay",
                                                default=False, visible=False, group="Track Map")
    track_map_ui_scale: float = ui_scale_field(description="Track map UI scale" )
    track_map_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle track map overlay UDP action code", visible=False, group="Track Map")

    # ============== INPUT TELEMETRY OVERLAY ==============
    show_input_overlay: bool = overlay_enable_field(description="Enable input telemetry overlay",
                                                    group="Input Telemetry")
    input_overlay_ui_scale: float = ui_scale_field(description="Input telemetry overlay UI scale")
    input_overlay_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle input telemetry overlay UDP action code", group="Input Telemetry")
    input_overlay_buffer_duration_sec: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Input telemetry overlay buffer duration (sec)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True,
                "group": "Input Telemetry",
                "ext_info": [
                    "Controls how much recent throttle, brake, and steering input history is shown in the overlay. "
                    "Higher values show a longer time window, while lower values make input changes appear more responsive.\n"
                    "Test out different values in heavy braking zones. Set a value where you can see the braking shape once you've exited the corner.\n"
                    "Recommendation: Bahrain T1"
                ]
            }
        }
    )

    # ============== TRACK RADAR OVERLAY ==============
    show_track_radar_overlay: bool = overlay_enable_field(description="Enable track radar overlay", group="Track Radar")
    track_radar_overlay_ui_scale: float = ui_scale_field(description="Track radar overlay UI scale")
    track_radar_overlay_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle track radar overlay UDP action code", group="Track Radar")
    track_radar_idle_opacity: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Track radar overlay idle opacity percentage",
        json_schema_extra={
            "ui": {
                "type" : "slider",
                "visible": False,
                "min": 0,
                "max": 100,
                "ext_info": [
                    'Track Radar opacity when no other cars are nearby'
                ]
            }
        }
    )

    # ============== GLOBAL OVERLAY CONTROLS ==============

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
                "max": 100,
                "group": "Global Controls"
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

    def model_post_init(self, __context: Any) -> None:  # pylint: disable=arguments-differ
        # Normalize / merge layout unconditionally
        self.layout = merge_overlay_layout(self.layout)

    @model_validator(mode="after")
    def validate_hud_settings(self):
        # If HUD is disabled, no further validation applies
        if not self.enabled:
            return self

        # ---- At least one overlay must be enabled ----
        if not any(
            getattr(self, field_name)
            for field_name, field in type(self).model_fields.items()
            if field.json_schema_extra.get("ui", {}).get("overlay_enable", False)
        ):
            raise ValueError(
                "HUD cannot be enabled while all overlays are disabled"
            )

        # ---- MFD pages must exist if MFD is enabled ----
        if self.show_mfd and not self.mfd_settings.sorted_enabled_pages():
            raise ValueError(
                "HUD cannot be enabled while all MFD pages are disabled"
            )

        # ---- Opacity relationship ----
        if self.track_radar_idle_opacity > self.overlays_opacity:
            raise ValueError(
                "Track radar idle opacity cannot be greater than overlays opacity"
            )

        return self

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
    def get_layout_dict_from_json(cls, json_dict: Dict[str, Dict[str, int]]) -> Dict[str, OverlayPosition]:
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
