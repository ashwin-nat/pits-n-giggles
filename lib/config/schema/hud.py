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
from copy import deepcopy
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .diff import ConfigDiffMixin
from .utils import udp_action_field

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_UI_META_UI_SCALE = {
    "ui": {
        "type": "slider",
        "visible": False,
        "min_ui": 50,
        "max_ui": 200,
        "convert": "percent",
        "unit": "%"
    }
}

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class MfdPageSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {"visible": True}

    enabled: bool = Field(
        default=False,
        description="Enable this MFD page",
        json_schema_extra={"ui": {"type": "check_box", "visible": True}},
    )

    position: int = Field(
        gt=0,
        description="Ordering index",
        json_schema_extra={"ui": {"type": "text_box", "visible": True}},
    )


DEFAULT_PAGES = {
    "lap_times": MfdPageSettings(enabled=True, position=1, description="Lap Times"),
    "weather_forecast": MfdPageSettings(enabled=True, position=2, description="Weather Forecast"),
    "fuel_info": MfdPageSettings(enabled=True, position=3, description="Fuel Info"),
    "tyre_info": MfdPageSettings(enabled=True, position=4, description="Tyre Info"),
    "pit_rejoin": MfdPageSettings(enabled=True, position=5, description="Pit Rejoin"),
    "tyre_sets": MfdPageSettings(enabled=True, position=6, description="Tyre Sets"),
}


class MfdSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {"visible": True}

    pages: Dict[str, MfdPageSettings] = Field(
        default_factory=lambda: copy.deepcopy(DEFAULT_PAGES),
        description="Dictionary of MFD pages",
        json_schema_extra={
            "ui": {
                "type": "group_box",
                "visible": True,
                "reorderable_collection": True,
                "item_enabled_field": "enabled",
                "item_position_field": "position"
            }
        },
    )

    @model_validator(mode="after")
    def check_unique_positions(self):
        # Enabled pages must have unique positions
        pos_map = {} # Key = position, Value = page
        for name, page in self.pages.items():
            if not page.enabled:
                continue
            if page.position in pos_map:
                raise ValueError(
                    f"MFD page '{name}' has duplicate position {page.position} "
                    f"(also used by '{pos_map[page.position]}')"
                )
            pos_map[page.position] = name

        return self

    @model_validator(mode="after")
    def add_missing_pages(self):
        """
        Ensure all DEFAULT_PAGES exist.
        New pages are added as disabled by default.
        """
        merged = dict(self.pages)

        for key, default_page in DEFAULT_PAGES.items():
            if key not in merged:
                # Add new page, but disabled so UI does not break
                new_page = default_page.model_copy(deep=True)
                new_page.enabled = False
                merged[key] = new_page

        self.pages = merged
        return self

    def sorted_enabled_pages(self):
        return sorted(
            [(name, page) for name, page in self.pages.items() if page.enabled],
            key=lambda p: p[1].position
        )

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
    lap_timer_ui_scale: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Lap Timer UI scale",
        json_schema_extra=deepcopy(_UI_META_UI_SCALE)
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
    timing_tower_ui_scale: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Timing tower UI scale",
        json_schema_extra=deepcopy(_UI_META_UI_SCALE)
    )
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
    mfd_ui_scale: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="MFD UI scale",
        json_schema_extra=deepcopy(_UI_META_UI_SCALE)
    )
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

    toggle_overlays_udp_action_code: Optional[int] = udp_action_field(
        "The UDP custom action code to show/hide overlays")
    cycle_mfd_udp_action_code: Optional[int] = udp_action_field(
        "The UDP custom action code to cycle MFD pages")

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
