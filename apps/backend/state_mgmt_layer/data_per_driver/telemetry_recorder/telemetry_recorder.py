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
    RecordedSensor(SensorConfig("throttle", "Throttle", "%", SensorType.CONTINUOUS), attrgetter("throttle")),
    RecordedSensor(SensorConfig("brake", "Brake", "%", SensorType.CONTINUOUS), attrgetter("brake")),
    RecordedSensor(SensorConfig("steering", "Steering", "", SensorType.CONTINUOUS), attrgetter("steering")),
    RecordedSensor(SensorConfig("speed", "Speed", "km/h", SensorType.CONTINUOUS), attrgetter("speed")),
    RecordedSensor(SensorConfig("gear", "Gear", "", SensorType.DISCRETE), attrgetter("gear")),
    RecordedSensor(SensorConfig("engine_rpm", "Engine RPM", "rpm", SensorType.CONTINUOUS), attrgetter("engine_rpm")),
    RecordedSensor(SensorConfig("ers.deploy_mode", "ERS Deploy Mode", "", SensorType.DISCRETE),
                   attrgetter("ers_deploy_mode")),
    RecordedSensor(SensorConfig("ers.store_energy", "ERS Store Energy", "J", SensorType.CONTINUOUS),
                   attrgetter("ers_store_energy")),
    RecordedSensor(SensorConfig("tyre_wear.fl", "Tyre Wear FL", "%", SensorType.CONTINUOUS),
                   attrgetter("tyre_wear_fl")),
    RecordedSensor(SensorConfig("tyre_wear.fr", "Tyre Wear FR", "%", SensorType.CONTINUOUS),
                   attrgetter("tyre_wear_fr")),
    RecordedSensor(SensorConfig("tyre_wear.rl", "Tyre Wear RL", "%", SensorType.CONTINUOUS),
                   attrgetter("tyre_wear_rl")),
    RecordedSensor(SensorConfig("tyre_wear.rr", "Tyre Wear RR", "%", SensorType.CONTINUOUS),
                   attrgetter("tyre_wear_rr")),
)