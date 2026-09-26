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
    throttle: Optional[float] = None   # 0.0-1.0
    brake: Optional[float] = None      # 0.0-1.0
    steering: Optional[float] = None   # -1.0 (full left) to 1.0 (full right)

    # Vehicle state
    speed: Optional[float] = None      # km/h
    gear: Optional[int] = None         # -1 = reverse, 0 = neutral, 1-8 = forward
    engine_rpm: Optional[float] = None

    # ERS
    ers_deploy_mode: Optional[int] = None  # ERSDeployMode.value; enum owned by the producer
    ers_store_energy: Optional[float] = None

    # Tyre wear
    tyre_wear_fl: Optional[float] = None
    tyre_wear_fr: Optional[float] = None
    tyre_wear_rl: Optional[float] = None
    tyre_wear_rr: Optional[float] = None

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

# The F1 sensor catalog: each entry's manifest description plus how to read its value
# off a TelemetrySnapshot.
F1_SENSORS: tuple[RecordedSensor[TelemetrySnapshot], ...] = (

    # ------- INPUTS -----------
    RecordedSensor(
        config=SensorConfig(
            key="throttle",
            label="Throttle",
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("throttle")),
    RecordedSensor(
        config=SensorConfig(
            key="brake",
            label="Brake",
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("brake")),
    RecordedSensor(
        config=SensorConfig(
            key="steering",
            label="Steering",
            unit="%",
            type=SensorType.CONTINUOUS),
        get=attrgetter("steering")),

    # ---- CAR STATE -----
    RecordedSensor(
        config=SensorConfig(
            key="gear",
            label="Gear",
            unit="",
            type=SensorType.DISCRETE,
            range=(-1, 8)), # -1 for reverse
        get=attrgetter("gear")),
    RecordedSensor(
        config=SensorConfig(
            key="speed",
            label="Speed",
            unit="kmph",
            type=SensorType.CONTINUOUS),
        get=attrgetter("speed")),
    RecordedSensor(
        config=SensorConfig(
            key="engine_rpm",
            label="Engine RPM",
            unit="rpm",
            type=SensorType.CONTINUOUS),
        get=attrgetter("engine_rpm")),

    # ------ ERS --------
    RecordedSensor(
        config=SensorConfig(
            key="ers.deploy_mode",
            label="ERS Deploy Mode",
            unit="",
            type=SensorType.DISCRETE,
            range=(0, 3)),
        get=attrgetter("ers_deploy_mode")),
    RecordedSensor(
        config=SensorConfig(
            key="ers.store_energy",
            label="ERS Store Energy",
            unit="J",
            type=SensorType.CONTINUOUS,
            range=(0, CarStatusData.MAX_ERS_STORE_ENERGY)),
        get=attrgetter("ers_store_energy")),

    # ------ TYRE WEAR -------
    RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.fl",
            label="Tyre Wear FL",
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_fl")),
    RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.fr",
            label="Tyre Wear FR",
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_fr")),
    RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.rl",
            label="Tyre Wear RL",
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_rl")),
    RecordedSensor(
        config=SensorConfig(
            key="tyre_wear.rr",
            label="Tyre Wear RR",
            unit="%",
            type=SensorType.CONTINUOUS,
            range=(0, 100)),
        get=attrgetter("tyre_wear_rr")),
)
