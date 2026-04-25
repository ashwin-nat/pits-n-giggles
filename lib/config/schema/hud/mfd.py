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
from typing import Any, ClassVar, Dict

from pydantic import BaseModel, Field, model_validator

from ..diff import ConfigDiffMixin

# ------------------------------------- CONSTANTS ----------------------------------------------------------------------

class MfdPageId(str, Enum):
    COLLAPSED        = "collapsed"
    LAP_TIMES        = "lap_times"
    WEATHER_FORECAST = "weather_forecast"
    FUEL_INFO        = "fuel_info"
    TYRE_INFO        = "tyre_info"
    PIT_REJOIN       = "pit_rejoin"
    TYRE_SETS        = "tyre_sets"
    PACE_COMP        = "pace_comp"

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
    MfdPageId.LAP_TIMES:        MfdPageSettings(enabled=True, position=1, description="Lap Times"),
    MfdPageId.WEATHER_FORECAST: MfdPageSettings(enabled=True, position=2, description="Weather Forecast"),
    MfdPageId.FUEL_INFO:        MfdPageSettings(enabled=True, position=3, description="Fuel Info"),
    MfdPageId.TYRE_INFO:        MfdPageSettings(enabled=True, position=4, description="Tyre Info"),
    MfdPageId.PIT_REJOIN:       MfdPageSettings(enabled=True, position=5, description="Pit Rejoin"),
    MfdPageId.TYRE_SETS:        MfdPageSettings(enabled=True, position=6, description="Tyre Sets"),
    MfdPageId.PACE_COMP:        MfdPageSettings(enabled=True, position=7, description="Pace Comparison"),
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
        New pages are added as disabled by default, with a non-conflicting position.
        """
        merged = dict(self.pages)
        used_positions = {page.position for page in merged.values()}

        for key, default_page in DEFAULT_PAGES.items():
            str_key = key.value if isinstance(key, MfdPageId) else key
            if str_key not in merged:
                new_page = default_page.model_copy(deep=True)
                new_page.enabled = False
                # Resolve position conflict: find the next free slot
                pos = new_page.position
                while pos in used_positions:
                    pos += 1
                new_page.position = pos
                used_positions.add(pos)
                merged[str_key] = new_page

        self.pages = merged
        return self

    def sorted_enabled_pages(self):
        return sorted(
            [(name, page) for name, page in self.pages.items() if page.enabled],
            key=lambda p: p[1].position
        )
