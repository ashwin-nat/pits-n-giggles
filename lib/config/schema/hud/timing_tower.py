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
from typing import Any, ClassVar, Dict, List, Tuple

from pydantic import BaseModel, Field, model_validator

from ..diff import ConfigDiffMixin

# ------------------------------------- CONSTANTS ----------------------------------------------------------------------

class TimingTowerColId(str, Enum):
    TEAM_LOGO     = "team_logo"
    DELTA         = "delta"
    TYRE          = "tyre"
    ERS_DRS       = "ers_drs"
    PENS          = "pens"
    TL_WARNS      = "tl_warns"
    BEST_LAP      = "best_lap"
    LAST_LAP      = "last_lap"
    WING_DMG      = "wing_dmg"
    SPEED_TRAP    = "speed_trap"
    FUEL          = "fuel"
    DRIVER_STATUS = "driver_status"

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class TimingTowerColSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {"visible": True}

    enabled: bool = Field(
        default=False,
        description="Enable this column",
        json_schema_extra={"ui": {"type": "check_box", "visible": True}},
    )

    position: int = Field(
        gt=0,
        description="Ordering index",
        json_schema_extra={"ui": {"type": "text_box", "visible": True}},
    )

    # Not stored in JSON — filled at runtime from DEFAULT_COLS by TimingTowerColOptions.fill_col_descriptions.
    description: str = Field(default="", exclude=True)


DEFAULT_COLS: Dict[TimingTowerColId, "TimingTowerColSettings"] = {
    TimingTowerColId.TEAM_LOGO: TimingTowerColSettings(
        enabled=True,  position=1,  description="Team logo"),
    TimingTowerColId.DELTA: TimingTowerColSettings(
        enabled=True,  position=2,  description="Delta"),
    TimingTowerColId.TYRE: TimingTowerColSettings(
        enabled=True,  position=3,  description="Tyre compound and wear"),
    TimingTowerColId.ERS_DRS: TimingTowerColSettings(
        enabled=True,  position=4,  description="ERS / DRS"),
    TimingTowerColId.PENS: TimingTowerColSettings(
        enabled=True,  position=5,  description="Penalties"),
    TimingTowerColId.TL_WARNS: TimingTowerColSettings(
        enabled=True,  position=6,  description="Track Limit warnings"),
    TimingTowerColId.BEST_LAP: TimingTowerColSettings(
        enabled=False, position=7,  description="Best Lap"),
    TimingTowerColId.LAST_LAP: TimingTowerColSettings(
        enabled=False, position=8,  description="Last Lap"),
    TimingTowerColId.WING_DMG: TimingTowerColSettings(
        enabled=False, position=9,  description="Front Wing Damage"),
    TimingTowerColId.SPEED_TRAP: TimingTowerColSettings(
        enabled=False, position=10, description="Speed Trap"),
    TimingTowerColId.FUEL: TimingTowerColSettings(
        enabled=False, position=11, description="Fuel level (surplus laps)"),
    TimingTowerColId.DRIVER_STATUS: TimingTowerColSettings(
        enabled=False, position=12,
        description="Driver status (e.g., IN_GARAGE, FLYING_LAP"),
}

class TimingTowerColOptions(ConfigDiffMixin, BaseModel):

    show_col_header: bool = Field(
        default=True,
        description="Show column header",
        json_schema_extra={"ui": {"type": "check_box"}}
    )

    cols: Dict[str, TimingTowerColSettings] = Field(
        default_factory=lambda: copy.deepcopy(DEFAULT_COLS),
        description="Column visibility and order",
        json_schema_extra={
            "ui": {
                "type": "group_box",
                "visible": True,
                "reorderable_collection": True,
                "item_enabled_field": "enabled",
                "item_position_field": "position",
                "item_label_field": "description",
            }
        },
    )

    @model_validator(mode="after")
    def check_unique_positions(self):
        pos_map: Dict[int, str] = {}
        for col_id, col in self.cols.items():
            if not col.enabled:
                continue
            if col.position in pos_map:
                raise ValueError(
                    f"Timing tower column '{col_id}' has duplicate position {col.position} "
                    f"(also used by '{pos_map[col.position]}')"
                )
            pos_map[col.position] = col_id
        return self

    @model_validator(mode="after")
    def add_missing_cols(self):
        """Ensure all DEFAULT_COLS entries are present.

        Any column absent from the stored config is added as disabled with a
        non-conflicting position.  This is the forward-compatibility hook that
        handles both version upgrades and future new-column additions.
        """
        merged = dict(self.cols)
        used_positions = {col.position for col in merged.values()}

        for col_id, default_col in DEFAULT_COLS.items():
            key = col_id.value if isinstance(col_id, TimingTowerColId) else col_id
            if key not in merged:
                new_col = default_col.model_copy(deep=True)
                new_col.enabled = False
                pos = new_col.position
                while pos in used_positions:
                    pos += 1
                new_col.position = pos
                used_positions.add(pos)
                merged[key] = new_col

        self.cols = merged
        return self

    @model_validator(mode="after")
    def fill_col_descriptions(self):
        """Populate the excluded description field on every known column from DEFAULT_COLS.

        Because description is excluded from JSON serialisation, it is always "" after a
        round-trip through the config file.  This validator re-stamps the canonical
        description onto every column so callers can read col.description at runtime.
        """
        for col_id, default_col in DEFAULT_COLS.items():
            key = col_id.value if isinstance(col_id, TimingTowerColId) else col_id
            if key in self.cols:
                self.cols[key].description = default_col.description
        return self

    def sorted_enabled_cols(self) -> List[Tuple[str, TimingTowerColSettings]]:
        """Return enabled columns sorted by position, ascending."""
        return sorted(
            [(col_id, col) for col_id, col in self.cols.items() if col.enabled],
            key=lambda p: p[1].position
        )
