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
from typing import Optional

from lib.pngt import BaseTelemetrySnapshot

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(slots=True)
class TelemetrySnapshot(BaseTelemetrySnapshot):
    """A strongly typed snapshot of all available F1 sensor values at a single point in
    time, passed to lib.pngt.DriverTelemetryRecorder.update() on every telemetry packet.
    The caller populates whatever fields the sim reported for this packet; the recorder
    filters internally to the sensors it was configured to record via SensorMapper.

    Every field below (other than the inherited, mandatory `lap_distance` and
    `lap_time_ms`) is F1-domain-specific, which is why this subclass lives here
    in apps/backend rather than in lib/pngt/ingest -- that package only owns the
    core fields every snapshot must carry (see BaseTelemetrySnapshot); everything
    else here is read through a SensorMapper implementation this app also owns.

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
    gear: Optional[int] = None         # 0 = reverse, 1-8 = forward
    engine_rpm: Optional[float] = None

    # ERS
    ers_deploy_mode: Optional[int] = None  # ERSDeployMode.value; enum owned by the producer
    ers_store_energy: Optional[float] = None

    # Tyre wear
    tyre_wear_fl: Optional[float] = None
    tyre_wear_fr: Optional[float] = None
    tyre_wear_rl: Optional[float] = None
    tyre_wear_rr: Optional[float] = None
