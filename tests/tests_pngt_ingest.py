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

import os
import sys
from typing import Optional, Union

import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.pngt import SensorDtype, SensorMapper, TelemetrySnapshot

# ----------------------------------------------------------------------------------------------------------------------
# Test-only SensorMapper implementations
#
# Neither ships as part of the library: a real sensor catalog is domain-specific and
# belongs with whatever code actually populates TelemetrySnapshot from real packets
# (see mapper.py's docstring), and a mapper that returns pre-set values regardless of
# the snapshot has no purpose outside exercising DriverTelemetryRecorder's own logic.
# ----------------------------------------------------------------------------------------------------------------------

class StubSensorMapper(SensorMapper):
    """Returns whatever value was injected for a sensor key, ignoring the snapshot
    entirely. Lets recorder tests exercise buffering/flashback/export logic without any
    real TelemetrySnapshot field names. get_value() defaults an unconfigured key to
    None (test convenience -- a recorder test rarely wants to declare every possible
    key up front); get_dtype() raises for one instead, since that's the call recorder
    construction uses to fail fast on a genuinely unknown sensor key."""

    def __init__(
        self,
        values: dict[str, Optional[Union[float, int]]],
        dtypes: Optional[dict[str, SensorDtype]] = None,
    ) -> None:
        self._values = values
        self._dtypes = dtypes or {}

    def get_value(
        self,
        snapshot: TelemetrySnapshot,
        sensor_key: str,
    ) -> Optional[Union[float, int]]:
        return self._values.get(sensor_key)

    def get_dtype(self, sensor_key: str) -> SensorDtype:
        try:
            return self._dtypes[sensor_key]
        except KeyError as exc:
            raise KeyError(f"Unknown sensor key {sensor_key!r}") from exc


class ExampleSensorMapper(SensorMapper):
    """Minimal real-field mapper, for testing SensorMapper's contract itself (as opposed
    to StubSensorMapper's pre-set values) against a real TelemetrySnapshot."""

    _MAP = {
        "speed": ("speed", SensorDtype.FLOAT32),
        "gear": ("gear", SensorDtype.INT8),
    }

    def get_value(
        self,
        snapshot: TelemetrySnapshot,
        sensor_key: str,
    ) -> Optional[Union[float, int]]:
        field_name, _ = self._resolve(sensor_key)
        return getattr(snapshot, field_name)

    def get_dtype(self, sensor_key: str) -> SensorDtype:
        _, dtype = self._resolve(sensor_key)
        return dtype

    def _resolve(self, sensor_key: str):
        try:
            return self._MAP[sensor_key]
        except KeyError as exc:
            raise KeyError(f"Unknown sensor key {sensor_key!r}") from exc

# ----------------------------------------------------------------------------------------------------------------------
# SensorMapper
# ----------------------------------------------------------------------------------------------------------------------

def test_sensor_mapper_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        SensorMapper()  # pylint: disable=abstract-class-instantiated


def test_example_sensor_mapper_resolves_configured_keys():
    mapper = ExampleSensorMapper()
    snapshot = TelemetrySnapshot(lap_distance=0.0, speed=245.1, gear=6)

    assert mapper.get_value(snapshot, "speed") == 245.1
    assert mapper.get_value(snapshot, "gear") == 6


def test_example_sensor_mapper_unknown_key_raises():
    mapper = ExampleSensorMapper()
    snapshot = TelemetrySnapshot(lap_distance=0.0)

    with pytest.raises(KeyError):
        mapper.get_value(snapshot, "not_a_real_sensor")


def test_example_sensor_mapper_resolves_dtype():
    mapper = ExampleSensorMapper()

    assert mapper.get_dtype("speed") == SensorDtype.FLOAT32
    assert mapper.get_dtype("gear") == SensorDtype.INT8


def test_example_sensor_mapper_unknown_key_raises_on_dtype():
    mapper = ExampleSensorMapper()

    with pytest.raises(KeyError):
        mapper.get_dtype("not_a_real_sensor")

# ----------------------------------------------------------------------------------------------------------------------
# StubSensorMapper
# ----------------------------------------------------------------------------------------------------------------------

def test_stub_sensor_mapper_returns_injected_values():
    mapper = StubSensorMapper({"speed": 123.4, "gear": 3, "drs": None})
    snapshot = TelemetrySnapshot(lap_distance=0.0)  # never consulted

    assert mapper.get_value(snapshot, "speed") == 123.4
    assert mapper.get_value(snapshot, "gear") == 3
    assert mapper.get_value(snapshot, "drs") is None


def test_stub_sensor_mapper_missing_key_returns_none():
    mapper = StubSensorMapper({"speed": 100.0})
    snapshot = TelemetrySnapshot(lap_distance=0.0)

    assert mapper.get_value(snapshot, "not_configured") is None


def test_stub_sensor_mapper_returns_injected_dtype():
    mapper = StubSensorMapper({"speed": 100.0}, dtypes={"speed": SensorDtype.FLOAT32})

    assert mapper.get_dtype("speed") == SensorDtype.FLOAT32


def test_stub_sensor_mapper_missing_dtype_raises():
    mapper = StubSensorMapper({"speed": 100.0})

    with pytest.raises(KeyError):
        mapper.get_dtype("speed")
