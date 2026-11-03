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
    POSITION = "Position"
    ALL = "All"

class SensorGroup(str, Enum):
    DRIVER_INPUTS = "Driver Inputs"
    CAR_STATE = "Car State"
    ERS = "ERS"
    TYRE_WEAR = "Tyre Wear"
    MOTION = "Motion"
    TYRE_STATUS = "Tyre Status"

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Optional group tooltips. A group without an entry gets no tooltip.
SENSOR_GROUP_INFO: Dict[SensorGroup, str] = {
    SensorGroup.ERS: "Energy recovery system state: deploy mode and battery charge",
    SensorGroup.TYRE_STATUS: "Per-tyre temperatures and pressure, and the surface under each wheel",
    SensorGroup.MOTION: "Car world position and heading (yaw)",
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def sensor_field(*, label: str, group: SensorGroup, restricted: bool,
                 presets: Set[SensorPreset], info: Optional[str] = None, visible: bool = True) -> Any:
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
                "visible": visible,
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

    # Tyre status
    tyre_surface_temp_fl: bool = sensor_field(
        label="Tyre Surface Temp FL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front left tyre surface temperature in °C")
    tyre_surface_temp_fr: bool = sensor_field(
        label="Tyre Surface Temp FR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front right tyre surface temperature in °C")
    tyre_surface_temp_rl: bool = sensor_field(
        label="Tyre Surface Temp RL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear left tyre surface temperature in °C")
    tyre_surface_temp_rr: bool = sensor_field(
        label="Tyre Surface Temp RR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear right tyre surface temperature in °C")
    tyre_inner_temp_fl: bool = sensor_field(
        label="Tyre Inner Temp FL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front left tyre inner temperature in °C")
    tyre_inner_temp_fr: bool = sensor_field(
        label="Tyre Inner Temp FR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front right tyre inner temperature in °C")
    tyre_inner_temp_rl: bool = sensor_field(
        label="Tyre Inner Temp RL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear left tyre inner temperature in °C")
    tyre_inner_temp_rr: bool = sensor_field(
        label="Tyre Inner Temp RR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear right tyre inner temperature in °C")
    tyre_pressure_fl: bool = sensor_field(
        label="Tyre Pressure FL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front left tyre pressure in PSI")
    tyre_pressure_fr: bool = sensor_field(
        label="Tyre Pressure FR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Front right tyre pressure in PSI")
    tyre_pressure_rl: bool = sensor_field(
        label="Tyre Pressure RL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear left tyre pressure in PSI")
    tyre_pressure_rr: bool = sensor_field(
        label="Tyre Pressure RR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Rear right tyre pressure in PSI")
    surface_type_fl: bool = sensor_field(
        label="Surface Type FL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Driving surface under the front left wheel")
    surface_type_fr: bool = sensor_field(
        label="Surface Type FR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Driving surface under the front right wheel")
    surface_type_rl: bool = sensor_field(
        label="Surface Type RL", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Driving surface under the rear left wheel")
    surface_type_rr: bool = sensor_field(
        label="Surface Type RR", group=SensorGroup.TYRE_STATUS, restricted=False,
        presets={SensorPreset.ADVANCED, SensorPreset.ALL},
        info="Driving surface under the rear right wheel")

    # Motion
    motion_pos_x: bool = sensor_field(
        label="Position X", group=SensorGroup.MOTION, restricted=False,
        presets={SensorPreset.POSITION, SensorPreset.ALL},
        info="World space X position in metres", visible=False)
    motion_pos_y: bool = sensor_field(
        label="Position Y", group=SensorGroup.MOTION, restricted=False,
        presets={SensorPreset.POSITION, SensorPreset.ALL},
        info="World space Y position in metres", visible=False)
    motion_pos_z: bool = sensor_field(
        label="Position Z", group=SensorGroup.MOTION, restricted=False,
        presets={SensorPreset.POSITION, SensorPreset.ALL},
        info="World space Z position in metres", visible=False)
    motion_yaw: bool = sensor_field(
        label="Yaw", group=SensorGroup.MOTION, restricted=False,
        presets={SensorPreset.POSITION, SensorPreset.ALL},
        info="Yaw angle in radians", visible=False)

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
