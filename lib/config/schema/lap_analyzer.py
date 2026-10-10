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

# -------------------------------------- ENUMS -------------------------------------------------------------------------

class SensorEntropy(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SensorPreset(str, Enum):
    BEGINNER = "Beginner"
    ADVANCED = "Advanced"

class SensorGroup(str, Enum):
    DRIVER_INPUTS = "Driver Inputs"
    CAR_STATE = "Car State"
    ERS = "ERS"
    TYRE_WEAR = "Tyre Wear"

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Compressed bytes per sample per entropy class. Calibrated by the calibrate-sensor-entropy skill.
ENTROPY_BYTES_PER_SAMPLE: Dict[SensorEntropy, float] = {
    SensorEntropy.VERY_LOW: 0.05,
    SensorEntropy.LOW: 0.4,
    SensorEntropy.MEDIUM: 0.7,
    SensorEntropy.HIGH: 2.1,
}

# Lap distance + lap time, always recorded
MANDATORY_BYTES_PER_SAMPLE = 4.65

# Optional group tooltips. A group without an entry gets no tooltip.
SENSOR_GROUP_INFO: Dict[SensorGroup, str] = {
    SensorGroup.ERS: "Energy recovery system state: deploy mode and battery charge",
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def sensor_field(*, label: str, group: SensorGroup, restricted: bool, entropy: SensorEntropy,
                 presets: Set[SensorPreset], info: Optional[str] = None):
    """
    Create a recordable sensor toggle. Defaults on iff it is in the Beginner preset.
    """
    return Field(
        default=SensorPreset.BEGINNER in presets,
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
                "entropy": entropy.value,
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
        entropy=SensorEntropy.MEDIUM,
        presets={SensorPreset.BEGINNER, SensorPreset.ADVANCED})
    brake: bool = sensor_field(
        label="Brake", group=SensorGroup.DRIVER_INPUTS, restricted=False,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.BEGINNER, SensorPreset.ADVANCED})
    steering: bool = sensor_field(
        label="Steering", group=SensorGroup.DRIVER_INPUTS, restricted=False,
        entropy=SensorEntropy.HIGH,
        presets={SensorPreset.BEGINNER, SensorPreset.ADVANCED})
    gear: bool = sensor_field(
        label="Gear", group=SensorGroup.CAR_STATE, restricted=False,
        entropy=SensorEntropy.VERY_LOW,
        presets={SensorPreset.BEGINNER, SensorPreset.ADVANCED})

    # Car state
    speed: bool = sensor_field(
        label="Speed", group=SensorGroup.CAR_STATE, restricted=False,
        entropy=SensorEntropy.MEDIUM,
        presets={SensorPreset.BEGINNER, SensorPreset.ADVANCED})
    engine_rpm: bool = sensor_field(
        label="Engine RPM", group=SensorGroup.CAR_STATE, restricted=False,
        entropy=SensorEntropy.HIGH,
        presets={SensorPreset.BEGINNER, SensorPreset.ADVANCED})

    # ERS
    ers_deploy_mode: bool = sensor_field(
        label="ERS Deploy Mode", group=SensorGroup.ERS, restricted=True,
        entropy=SensorEntropy.VERY_LOW,
        presets={SensorPreset.ADVANCED})
    ers_store_energy_j: bool = sensor_field(
        label="ERS Store (J)", group=SensorGroup.ERS, restricted=True,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.ADVANCED},
        info="Energy in the ERS battery, in joules")
    ers_store_energy_perc: bool = sensor_field(
        label="ERS Store Percentage", group=SensorGroup.ERS, restricted=True,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.ADVANCED},
        info="ERS battery charge as a percentage of capacity (4 MJ)")

    # Tyre wear
    tyre_wear_fl: bool = sensor_field(
        label="Tyre Wear FL", group=SensorGroup.TYRE_WEAR, restricted=True,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.ADVANCED},
        info="Front left tyre wear %")
    tyre_wear_fr: bool = sensor_field(
        label="Tyre Wear FR", group=SensorGroup.TYRE_WEAR, restricted=True,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.ADVANCED},
        info="Front right tyre wear %")
    tyre_wear_rl: bool = sensor_field(
        label="Tyre Wear RL", group=SensorGroup.TYRE_WEAR, restricted=True,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.ADVANCED},
        info="Rear left tyre wear %")
    tyre_wear_rr: bool = sensor_field(
        label="Tyre Wear RR", group=SensorGroup.TYRE_WEAR, restricted=True,
        entropy=SensorEntropy.LOW,
        presets={SensorPreset.ADVANCED},
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
    record_in_race: bool = Field(
        default=True,
        description="Record laps during race sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    record_in_quali: bool = Field(
        default=True,
        description="Record laps during qualifying sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    record_in_fp: bool = Field(
        default=False,
        description="Record laps during free practice sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    record_in_tt: bool = Field(
        default=False,
        description="Record laps during time trial sessions",
        json_schema_extra={
            "ui": {
                "type" : "check_box",
                "visible": True
            }
        }
    )
    Sensors: LapAnalyzerSensorSettings = Field(
        default_factory=LapAnalyzerSensorSettings,
        description="Sensors",
    )
