# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from enum import Enum
from typing import Any, ClassVar, Dict, Optional, Set

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin
from .utils import check_box_row_field

# -------------------------------------- ENUMS -------------------------------------------------------------------------

class SensorPreset(str, Enum):
    MINIMAL = "Minimal"
    DEFAULT = "Default"
    ADVANCED = "Advanced"
    ALL = "All"

class SensorGroup(str, Enum):
    DRIVER_INPUTS = "Driver Inputs"
    CAR_STATE = "Car State"
    ERS = "ERS"
    TYRE_WEAR = "Tyre Wear"

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Optional group tooltips. A group without an entry gets no tooltip.
SENSOR_GROUP_INFO: Dict[SensorGroup, str] = {
    SensorGroup.ERS: "Energy recovery system state: deploy mode and battery charge",
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def sensor_field(*, label: str, group: SensorGroup, restricted: bool,
                 presets: Set[SensorPreset], info: Optional[str] = None):
    """
    Create a recordable sensor toggle. Defaults on iff it is in the Default preset.
    """
    assert label, "sensor_field needs a non-empty label, the launcher sorts and displays by it"
    return Field(
        default=SensorPreset.DEFAULT in presets,
        description=label,
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
            },
            "sensor": {
                "info": info,
                "group": group.value,
                "restricted": restricted,
                "presets": sorted(p.value for p in presets),
            },
        },
    )

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class LapAnalyzerSensorSettings(ConfigDiffMixin, BaseModel):

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
    }

    # Inputs
    throttle: bool = sensor_field(
        label="Throttle", group=SensorGroup.DRIVER_INPUTS, restricted=False,
        presets={SensorPreset.MINIMAL, SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})
    brake: bool = sensor_field(
        label="Brake", group=SensorGroup.DRIVER_INPUTS, restricted=False,
        presets={SensorPreset.MINIMAL, SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})
    steering: bool = sensor_field(
        label="Steering", group=SensorGroup.DRIVER_INPUTS, restricted=False,
        presets={SensorPreset.MINIMAL, SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})

    # Car state
    gear: bool = sensor_field(
        label="Gear", group=SensorGroup.CAR_STATE, restricted=False,
        presets={SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})
    speed: bool = sensor_field(
        label="Speed", group=SensorGroup.CAR_STATE, restricted=False,
        presets={SensorPreset.MINIMAL, SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})
    engine_rpm: bool = sensor_field(
        label="Engine RPM", group=SensorGroup.CAR_STATE, restricted=False,
        presets={SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})

    # ERS
    ers_deploy_mode: bool = sensor_field(
        label="ERS Deploy Mode", group=SensorGroup.ERS, restricted=True,
        presets={SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL})
    ers_store_energy_j: bool = sensor_field(
        label="ERS Store (J)", group=SensorGroup.ERS, restricted=True,
        presets={SensorPreset.ALL},
        info="Energy in the ERS battery, in joules")
    ers_store_energy_perc: bool = sensor_field(
        label="ERS Store Percentage", group=SensorGroup.ERS, restricted=True,
        presets={SensorPreset.DEFAULT, SensorPreset.ADVANCED, SensorPreset.ALL},
        info="ERS battery charge as a percentage of capacity (4 MJ)")

    # Tyre wear
    tyre_wear_fl: bool = sensor_field(
        label="Tyre Wear FL", group=SensorGroup.TYRE_WEAR, restricted=True,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front left tyre wear %")
    tyre_wear_fr: bool = sensor_field(
        label="Tyre Wear FR", group=SensorGroup.TYRE_WEAR, restricted=True,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front right tyre wear %")
    tyre_wear_rl: bool = sensor_field(
        label="Tyre Wear RL", group=SensorGroup.TYRE_WEAR, restricted=True,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear left tyre wear %")
    tyre_wear_rr: bool = sensor_field(
        label="Tyre Wear RR", group=SensorGroup.TYRE_WEAR, restricted=True,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear right tyre wear %")

class LapAnalyzerSettings(ConfigDiffMixin, BaseModel):

    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible" : True,
        "page_type" : "lap_analyzer",
    }

    enable: bool = Field(
        default=True,
        description="Enable lap analyzer",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    record_other_cars: bool = Field(
        default=True,
        description="Record other cars' laps",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    record_in_spectator_mode: bool = Field(
        default=False,
        description="Record laps while spectating",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True,
                "ext_info" : [
                    "Records all cars in the session if enabled"
                ],
            }
        }
    )
    record_in_race: bool = check_box_row_field(
        "Record laps during race sessions", default=True,
        row="Record laps during", row_label="Race")
    record_in_quali: bool = check_box_row_field(
        "Record laps during qualifying sessions", default=True,
        row="Record laps during", row_label="Qualifying")
    record_in_fp: bool = check_box_row_field(
        "Record laps during free practice sessions", default=False,
        row="Record laps during", row_label="Free Practice")
    record_in_tt: bool = check_box_row_field(
        "Record laps during time trial sessions", default=False,
        row="Record laps during", row_label="Time Trial")
    Sensors: LapAnalyzerSensorSettings = Field(
        default_factory=LapAnalyzerSensorSettings,
        description="Sensors",
    )
