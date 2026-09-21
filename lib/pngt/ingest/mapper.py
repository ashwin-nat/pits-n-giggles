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

from abc import ABC, abstractmethod
from typing import Optional, Union

from ..dtypes import SensorDtype
from .dto import BaseTelemetrySnapshot

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SensorMapper(ABC):
    """Maps dotted sensor keys to values extracted from a snapshot object, and to their
    storage-width dtype. DriverTelemetryRecorder is completely decoupled from the
    snapshot's actual field names -- it only ever calls get_value()/get_dtype() with the
    dotted keys from TelemetryRecorderConfig.sensors, never touches a snapshot attribute
    directly except lap_distance (see BaseTelemetrySnapshot). A sensor's dtype has exactly one
    source of truth here, on the mapper -- not a second, independently-declared field
    elsewhere that could drift out of agreement with it.

    A real sensor catalog (e.g. one covering every F1 telemetry field), and the concrete
    snapshot dataclass it reads from, are both game-/domain-specific and belong with
    whatever code actually populates that snapshot from real packets -- e.g.
    apps/backend's own TelemetrySnapshot -- not in this generic library. A minimal
    concrete implementation, mapping two sensors:

        class ExampleSensorMapper(SensorMapper):
            _MAP = {
                "speed": ("speed", SensorDtype.FLOAT32),
                "gear": ("gear", SensorDtype.INT8),
            }

            def get_value(self, snapshot, sensor_key):
                field_name, _ = self._resolve(sensor_key)
                return getattr(snapshot, field_name)

            def get_dtype(self, sensor_key):
                _, dtype = self._resolve(sensor_key)
                return dtype

            def _resolve(self, sensor_key):
                try:
                    return self._MAP[sensor_key]
                except KeyError as exc:
                    raise KeyError(f"Unknown sensor key {sensor_key!r}") from exc

    A stub returning pre-set values regardless of the snapshot -- for exercising
    DriverTelemetryRecorder's buffering/flashback/export logic without any real
    field names -- lives in tests/tests_pngt_ingest.py, not here; it has no reason
    to ship as part of this library's public surface.
    """

    @abstractmethod
    def get_value(
        self,
        snapshot: BaseTelemetrySnapshot,
        sensor_key: str,
    ) -> Optional[Union[float, int]]:
        """Return the value for sensor_key from snapshot. Return None if the value is
        unavailable for this snapshot (the sim didn't report it this packet). Raise if
        sensor_key isn't a sensor this mapper knows how to resolve at all -- a
        recorder-config error, not a per-packet condition."""

    @abstractmethod
    def get_dtype(self, sensor_key: str) -> SensorDtype:
        """Return the storage-width dtype for sensor_key -- used to pick the
        missing-value sentinel (float('nan') vs -1) when get_value() returns None, and
        later by whatever assembles write_session()'s dtypes argument. Raise if
        sensor_key isn't known to this mapper, same as get_value()."""
