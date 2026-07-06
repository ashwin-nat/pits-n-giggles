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
from ..utils import overlay_enable_field, udp_action_field
from .layout import (DEFAULT_OVERLAY_LAYOUT, OverlayId, OverlayPosition,
                     merge_overlay_layout)
from .mfd import MfdSettings
from .timing_tower import TimingTowerColOptions

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class WeatherMFDUIType(str, Enum):
    CARDS = "Cards"
    GRAPH = "Graph"

class OverlaysSpeedUnit(str, Enum):
    KMPH = "km/h"
    MPH = "mph"

class OverlaysFuelEstimationMode(str, Enum):
    LINEAR_REGRESSION = "Linear regression"
    GAME_BUILT_IN = "Game built-in"

class MfdTyreWearRateType(str, Enum):
    MAX = "Max"
    AVERAGE = "Average"

class HudSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible": True,
        "page_type": "overlay",
    }

    enabled: bool = Field(
        default=True,
        description="Enable Overlays",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info": [
                    "only on Windows, setting will be ignored on other OS's",
                    'Recommended to also configure "Toggle all overlays UDP action code"'
                ]
            }
        }
    )
    toggle_overlays_udp_action_code: Optional[int] = udp_action_field("Toggle all overlays UDP action code")
    use_windowed_overlays: bool = Field(
        default=False,
        description="Use Windowed Overlays",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info": [
                    "Required for OBS window capture"
                ]
            }
        }
    )
    overlays_speed_unit: OverlaysSpeedUnit = Field(
        default=OverlaysSpeedUnit.KMPH,
        description="Speed unit",
        json_schema_extra={
            "ui": {
                "type": "radio_buttons",
                "options": [e.value for e in OverlaysSpeedUnit],
                "visible": True,
            }
        }
    )
    overlays_fuel_estimation_mode: OverlaysFuelEstimationMode = Field(
        default=OverlaysFuelEstimationMode.LINEAR_REGRESSION,
        description="Surplus fuel estimation technique",
        json_schema_extra={
            "ui": {
                "type": "radio_buttons",
                "options": [e.value for e in OverlaysFuelEstimationMode],
                "visible": True,
                "ext_info": [
                    "The game's built-in fuel estimation assumes a fixed fuel burn rate, regardless of driving style or track conditions. "
                    "\nLinear regression technique factors in the live fuel burn rate and can adapt to various situations, "
                    "\nsuch as safety cars, changing weather conditions, or aggressive vs. conservative driving styles. "
                ]
            }
        }
    )

    # ============== LAP TIMER OVERLAY ==============
    show_lap_timer: bool = overlay_enable_field(description="Enable lap timer overlay", group="Lap Timer",
                                               preview_image="assets/overlay-previews/lap-timer.png")
    lap_timer_minimal: bool = Field(
        default=False,
        description="Use minimal lap timer overlay (shows only the current lap time)",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
                "group": "Lap Timer",
            }
        }
    )
    lap_timer_toggle_udp_action_code: Optional[int] = udp_action_field(description="Toggle lap timer overlay UDP action code",
                                                                        group="Lap Timer")

    # ============== TIMING TOWER OVERLAY ==============
    show_timing_tower: bool = overlay_enable_field(description="Enable timing tower overlay", group="Timing Tower",
                                                   preview_image="assets/overlay-previews/timing-tower.png")
    timing_tower_max_rows: int = Field(
        default=5,
        ge=1,
        le=24,
        description="Max timing tower rows (odd number, or 24 for all cars)",
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
    timing_tower_relative_best_last_lap: bool = Field(
        default=False,
        description="Relative best and last lap times",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
                "group": "Timing Tower",
                "ext_info": [
                    "Show best/last lap times relative to the player or selected reference driver"
                ]
            }
        }
    )
    timing_tower_combined_tl_pens: bool = Field(
        default=False,
        description="Combine track limit & penalties",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
                "group": "Timing Tower",
                "ext_info": [
                    "Combine track limit and penalties into a single column, showing the sum of both values."
                ]
            }
        }
    )
    timing_tower_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle timing tower overlay UDP action code", group="Timing Tower")

    # ============== MFD OVERLAY ==============
    show_mfd: bool = overlay_enable_field(description="Enable MFD overlay", group="MFD",
                                         preview_image="assets/overlay-previews/mfd.png",
                                         ext_info=[
        'Recommended to also configure at least the "Next MFD page UDP action code" or '
        '"Previous MFD page UDP action code"'
    ])
    mfd_settings: MfdSettings = Field(
        default=MfdSettings(),
        description="MFD overlay settings",
        json_schema_extra={
            "ui": {
                "type" : "reorderable_view",
                "visible": True,
                "group": "MFD",
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
    mfd_tyre_wear_rate_type: MfdTyreWearRateType = Field(
        default=MfdTyreWearRateType.MAX,
        description="Tyre wear rate display mode for MFD (Tyre Wear Page)",
        json_schema_extra={
            "ui": {
                "type": "radio_buttons",
                "options": [e.value for e in MfdTyreWearRateType],
                "tooltips": {
                    "Max":     "The tyre with the max wear rate is displayed",
                    "Average": "The average wear rate of all tyres is displayed",
                },
                "visible": True,
                "group": "MFD",
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
        "Next MFD page UDP action code", group="MFD")
    prev_mfd_page_udp_action_code: Optional[int] = udp_action_field(
        "Previous MFD page UDP action code", group="MFD")

    # ============== TRACK MAP OVERLAY ==============
    show_track_map: bool = overlay_enable_field(description="Enable track map overlay",
                                                default=False, visible=False, group="Track Map",
                                                preview_image="assets/overlay-previews/track-map.png")
    track_map_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle track map overlay UDP action code", visible=False, group="Track Map")

    # ============== INPUT TELEMETRY OVERLAY ==============
    show_input_overlay: bool = overlay_enable_field(description="Enable input telemetry overlay",
                                                    group="Input Telemetry",
                                                    preview_image="assets/overlay-previews/input-telemetry.png")
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
    show_track_radar_overlay: bool = overlay_enable_field(description="Enable track radar overlay", group="Track Radar",
                                                          preview_image="assets/overlay-previews/track-radar.png")
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
    track_radar_range_m: int = Field(
        default=25,
        ge=5,
        le=35,
        description="Track radar display range in metres (half the radar area)",
        json_schema_extra={
            "ui": {
                "type": "slider",
                "visible": False,
                "min": 5,
                "max": 35,
                "ext_info": [
                    "Metres represented by the edge of the radar display"
                ]
            }
        }
    )

    # ============== HUD OVERLAY ==============
    show_hud_overlay: bool = overlay_enable_field(description="Enable HUD overlay", group="HUD Overlay",
                                                  preview_image="assets/overlay-previews/hud-overlay.png")
    hud_overlay_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle HUD overlay UDP action code", group="HUD Overlay")

    @property
    def hud_overlay_speed_unit_kmph(self) -> bool:
        """True if the speed unit is km/h"""
        return self.overlays_speed_unit == OverlaysSpeedUnit.KMPH

    @property
    def hud_overlay_speed_unit_mph(self) -> bool:
        """True if the speed unit is mph"""
        return self.overlays_speed_unit == OverlaysSpeedUnit.MPH

    @property
    def hud_overlay_fuel_estimation_linear_regression(self) -> bool:
        """True if fuel estimation uses linear regression"""
        return self.overlays_fuel_estimation_mode == OverlaysFuelEstimationMode.LINEAR_REGRESSION

    @property
    def hud_overlay_fuel_estimation_game_built_in(self) -> bool:
        """True if fuel estimation uses the game built-in value"""
        return self.overlays_fuel_estimation_mode == OverlaysFuelEstimationMode.GAME_BUILT_IN

    # ============== CIRCUIT INFO OVERLAY ==============
    show_circuit_info: bool = overlay_enable_field(
        description="Enable circuit info overlay",
        group="Circuit Info",
        preview_image="assets/overlay-previews/circuit-info.png",
        ext_info=[
            "The circuit info overlay is a progress bar that is divided into 3 sectors and \n"
            "shows the driver's current position on the track, as well as turn numbers and names. \n"
            "The sectors are also colour coded based on lap times (purple, green, yellow, red)"
        ])
    circuit_info_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle circuit info overlay UDP action code", group="Circuit Info")
    circuit_info_length: int = Field(
        default=800,
        ge=200,
        le=1500,
        description="Circuit info overlay circuit length fallback (m)",
        json_schema_extra={
            "ui": {
                "type": "slider",
                "visible": False,
                "min": 200,
                "max": 1500,
            }
        }
    )

    # ============== PU OVERLAY ==============
    show_pu_info: bool = overlay_enable_field(description="Enable power unit overlay", group="Power Unit",
                                             preview_image="assets/overlay-previews/power-unit.png")
    pu_display_harvest_info: bool = Field(
        default=False,
        description="Display harvest info in power unit overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Power Unit"}},
    )
    pu_toggle_udp_action_code: Optional[int] = udp_action_field(
        description="Toggle power unit overlay UDP action code", group="Power Unit")

    # ============== MFD PAGES (STANDALONE) ==============
    show_fuel_info: bool = overlay_enable_field(
        description="Enable fuel info standalone overlay",
        group="Fuel Info",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/fuel-info.png",
    )
    fuel_info_show_title: bool = Field(
        default=True,
        description="Show title bar in fuel info overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Fuel Info"}},
    )
    show_tyre_info: bool = overlay_enable_field(
        description="Enable tyre info standalone overlay",
        group="Tyre Info",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/tyre-info.png",
    )
    tyre_info_show_title: bool = Field(
        default=True,
        description="Show title bar in tyre info overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Tyre Info"}},
    )
    show_lap_times: bool = overlay_enable_field(
        description="Enable lap times history overlay",
        group="Lap Times",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/lap-times.png",
    )
    lap_times_show_title: bool = Field(
        default=True,
        description="Show title bar in lap times overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Lap Times"}},
    )
    show_weather: bool = overlay_enable_field(
        description="Enable weather forecast overlay",
        group="Weather",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/weather.png",
        ext_info=[
            "Use the MFD interact action (mfd_interaction_udp_action_code) to cycle through "
            "forecast sessions. If both the MFD weather page and this standalone overlay are "
            "enabled simultaneously, the interact button cycles both."
        ],
    )
    weather_show_title: bool = Field(
        default=True,
        description="Show title bar in weather forecast overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Weather"}},
    )
    show_pit_rejoin: bool = overlay_enable_field(
        description="Enable pit rejoin prediction overlay",
        group="Pit Rejoin",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/pit-rejoin.png",
    )
    pit_rejoin_show_title: bool = Field(
        default=True,
        description="Show title bar in pit rejoin prediction overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Pit Rejoin"}},
    )
    show_tyre_sets: bool = overlay_enable_field(
        description="Enable tyre sets overlay",
        group="Tyre Sets",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/tyre-sets.png",
    )
    tyre_sets_show_title: bool = Field(
        default=True,
        description="Show title bar in tyre sets overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Tyre Sets"}},
    )
    show_pace_comp: bool = overlay_enable_field(
        description="Enable pace comparison overlay",
        group="Pace Comparison",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/pace-comp.png",
    )
    pace_comp_show_title: bool = Field(
        default=True,
        description="Show title bar in pace comparison overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Pace Comparison"}},
    )
    show_traffic_monitor: bool = overlay_enable_field(
        description="Enable traffic monitor overlay",
        group="Traffic Monitor",
        default=False,
        mfd_friendly=True,
        preview_image="assets/overlay-previews/traffic-monitor.png",
    )
    traffic_monitor_show_title: bool = Field(
        default=True,
        description="Show title bar in traffic monitor overlay",
        json_schema_extra={"ui": {"type": "check_box", "visible": True, "group": "Traffic Monitor"}},
    )

    # ============== AUTO-HIDE IN MENU ==============
    auto_hide_in_menu: bool = Field(
        default=True,
        description="Auto-hide overlays when the game is in a menu",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
            }
        }
    )
    menu_silence_threshold_sec: float = Field(
        default=3.0,
        ge=1.0,
        le=30.0,
        description="Menu detection threshold (seconds)",
        json_schema_extra={
            "ui": {
                "type" : "text_box",
                "visible": True,
                "ext_info": [
                    "How long (in seconds) the backend must receive no periodic telemetry packets "
                    "before treating the game as being in a menu and hiding the overlays."
                ],
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
            },
            "diff_exclude": True,
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
        if self.track_radar_idle_opacity >= self.overlays_opacity:
            raise ValueError(
                "Track radar idle opacity cannot be greater than or equal to overlays opacity"
            )

        return self

    @field_validator("timing_tower_max_rows")
    def must_be_odd(cls, v): # pylint: disable=no-self-argument
        if (v != 24) and ((v % 2) == 0):
            raise ValueError("Timing tower max rows must be an odd number")
        return v

    @property
    def timing_tower_num_adjacent_cars(self) -> int:
        # Max rows already validated to be odd
        if self.timing_tower_max_rows == 24:
            return 12
        return (self.timing_tower_max_rows - 1) // 2

    @property
    def next_mfd_page_udp_action_code(self) -> Optional[int]:
        return self.cycle_mfd_udp_action_code

    def enabled_overlay_ids(self) -> list[OverlayId]:
        """Return the enabled overlays, in OverlayId declaration order."""
        enabled = {
            OverlayId.LAP_TIMER:       self.show_lap_timer,
            OverlayId.TIMING_TOWER:    self.show_timing_tower,
            OverlayId.MFD:             self.show_mfd,
            OverlayId.INPUT_TELEMETRY: self.show_input_overlay,
            OverlayId.TRACK_RADAR:     self.show_track_radar_overlay,
            OverlayId.HUD:             self.show_hud_overlay,
            OverlayId.CIRCUIT_INFO:    self.show_circuit_info,
            OverlayId.PU:              self.show_pu_info,
            OverlayId.FUEL_INFO:       self.show_fuel_info,
            OverlayId.TYRE_INFO:       self.show_tyre_info,
            OverlayId.LAP_TIMES:       self.show_lap_times,
            OverlayId.WEATHER:         self.show_weather,
            OverlayId.PIT_REJOIN:      self.show_pit_rejoin,
            OverlayId.TYRE_SETS:       self.show_tyre_sets,
            OverlayId.PACE_COMP:       self.show_pace_comp,
            OverlayId.TRAFFIC_MONITOR: self.show_traffic_monitor,
        }
        return [oid for oid, is_on in enabled.items() if is_on]

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
