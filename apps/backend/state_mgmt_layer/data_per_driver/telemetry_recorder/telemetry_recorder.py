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

from dataclasses import dataclass
from operator import attrgetter
from typing import Optional

from lib.config import LapAnalyzerSensorSettings
from lib.pngt import BaseTelemetrySnapshot, RecordedSensor, SensorConfig, SensorType
from lib.f1_types import CarStatusData

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(slots=True)
class TelemetrySnapshot(BaseTelemetrySnapshot):
    """A strongly typed snapshot of all available F1 sensor values at a single point in
    time, passed to lib.pngt.DriverTelemetryRecorder.update() on every telemetry packet.
    The caller populates whatever fields the sim reported for this packet; the recorder
    reads only the fields F1_SENSORS (below) names.

    Every field below (other than the inherited, mandatory `lap_distance` and
    `lap_time_ms`) is F1-domain-specific, which is why this subclass lives here in
    apps/backend rather than in lib/pngt -- that package only owns the core fields
    every snapshot must carry (see BaseTelemetrySnapshot).

    Ordered-int sensors (e.g. ERS deploy mode) are typed plain `int`, not an IntEnum --
    the enum itself is owned by whoever builds this snapshot from real sim packets, not
    by the recorder. This layer never inspects the int's meaning, only stores it.

    `slots=True`, matching the base class -- one instance per telemetry packet per
    driver at ~60 Hz, so skipping the __dict__ every plain instance would otherwise
    carry is a real saving at that volume, not a premature one.
    """
    # Driver inputs
    throttle: Optional[float] = None
    brake: Optional[float] = None
    steering: Optional[float] = None

    # Vehicle state
    speed: Optional[float] = None
    gear: Optional[int] = None
    engine_rpm: Optional[float] = None

    # ERS
    ers_deploy_mode: Optional[int] = None
    ers_store_energy_j: Optional[float] = None
    ers_store_energy_perc: Optional[float] = None

    # Tyre wear
    tyre_wear_fl: Optional[float] = None
    tyre_wear_fr: Optional[float] = None
    tyre_wear_rl: Optional[float] = None
    tyre_wear_rr: Optional[float] = None

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

def _label(field: str) -> str:
    """Manifest label for a LapAnalyzerSensorSettings field. A typo raises at import."""
    return LapAnalyzerSensorSettings.model_fields[field].description  # pylint: disable=unsubscriptable-object

# LapAnalyzerSensorSettings field name -> how to record it: manifest description plus how to
# read its value off a TelemetrySnapshot.
F1_SENSORS: dict[str, RecordedSensor[TelemetrySnapshot]] = {

    # ------- INPUTS -----------
    "throttle": RecordedSensor(
        config=SensorConfig(
            key="throttle",
            label=_label("throttle"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("throttle")),
    "brake": RecordedSensor(
        config=SensorConfig(
            key="brake",
            label=_label("brake"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("brake")),
    "steering": RecordedSensor(
        config=SensorConfig(
            key="steering",
            label=_label("steering"),
            unit="%",
            type=SensorType.CONTINUOUS),
        get=attrgetter("steering")),

    # ---- CAR STATE -----
    "gear": RecordedSensor(
        config=SensorConfig(
            key="gear",
            label=_label("gear"),
            unit="",
            type=SensorType.DISCRETE), # -1 for reverse
        get=attrgetter("gear")),
    "speed": RecordedSensor(
        config=SensorConfig(
            key="speed",
            label=_label("speed"),
            unit="kmph",
            type=SensorType.CONTINUOUS),
        get=attrgetter("speed")),
    "engine_rpm": RecordedSensor(
        config=SensorConfig(
            key="engine_rpm",
            label=_label("engine_rpm"),
            unit="rpm",
            type=SensorType.CONTINUOUS),
        get=attrgetter("engine_rpm")),

    # ------ ERS --------
    "ers_deploy_mode": RecordedSensor(
        config=SensorConfig(
            key="ers.deploy_mode",
            label=_label("ers_deploy_mode"),
            unit="",
            type=SensorType.DISCRETE,
            range=(0, 3)),
        get=attrgetter("ers_deploy_mode")),
    "ers_store_energy_j": RecordedSensor(
        config=SensorConfig(
            key="ers.store_energy_j",
            label=_label("ers_store_energy_j"),
            unit="J",
            type=SensorType.CONTINUOUS,
            range=(0, CarStatusData.MAX_ERS_STORE_ENERGY)),
        get=attrgetter("ers_store_energy_j")),
    "ers_store_energy_perc": RecordedSensor(
        config=SensorConfig(
            key="ers.store_energy",
            label=_label("ers_store_energy_perc"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("ers_store_energy_perc")),

    # ------ TYRE WEAR -------
    "tyre_wear_fl": RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.fl",
            label=_label("tyre_wear_fl"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_fl")),
    "tyre_wear_fr": RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.fr",
            label=_label("tyre_wear_fr"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_fr")),
    "tyre_wear_rl": RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.rl",
            label=_label("tyre_wear_rl"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_rl")),
    "tyre_wear_rr": RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.rr",
            label=_label("tyre_wear_rr"),
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_rr")),
}
