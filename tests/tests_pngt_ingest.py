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
from dataclasses import dataclass
from typing import Optional, Union

import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.pngt import (
    BaseTelemetrySnapshot,
    DriverTelemetryRecorder,
    IngestLapMetadata,
    SensorDtype,
    SensorMapper,
    TelemetryRecorderConfig,
)

# ----------------------------------------------------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------------------------------------------------

@dataclass(slots=True)
class _FakeSnapshot(BaseTelemetrySnapshot):
    """Test-only stand-in for a real snapshot object -- subclasses BaseTelemetrySnapshot
    the same way a real consumer's snapshot would (see apps/backend/state_mgmt_layer/data_per_driver's own
    TelemetrySnapshot), just with two fake sensor fields instead of ~40 real ones. This
    suite tests the generic lib.pngt.ingest layer, so it has no reason to depend on
    apps/backend's own (F1-specific) TelemetrySnapshot itself."""
    speed: Optional[float] = None
    gear: Optional[int] = None


def sample_lap_metadata(lap_number: int) -> IngestLapMetadata:
    """num_points=0 is a placeholder -- DriverTelemetryRecorder.on_lap_change() overwrites
    it; the caller has no way to know that count itself."""
    return IngestLapMetadata(
        lap_number=lap_number,
        lap_time_ms=90000,
        valid=True,
        tyre_compound="Soft",
        tyre_laps=lap_number,
        pit_in_lap=False,
        pit_out_lap=False,
        num_points=0,
    )

# ----------------------------------------------------------------------------------------------------------------------
# Test-only SensorMapper implementations
#
# Neither ships as part of the library: a real sensor catalog is domain-specific and
# belongs with whatever code actually populates a real snapshot from real packets
# (see mapper.py's docstring), and a mapper that returns pre-set values regardless of
# the snapshot has no purpose outside exercising DriverTelemetryRecorder's own logic.
# ----------------------------------------------------------------------------------------------------------------------

class StubSensorMapper(SensorMapper):
    """Returns whatever value was injected for a sensor key, ignoring the snapshot
    entirely. Lets recorder tests exercise buffering/flashback/export logic without any
    real snapshot field names. get_value() defaults an unconfigured key to
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
        snapshot: BaseTelemetrySnapshot,
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
    to StubSensorMapper's pre-set values) against a real snapshot object."""

    _MAP = {
        "speed": ("speed", SensorDtype.FLOAT32),
        "gear": ("gear", SensorDtype.INT8),
    }

    def get_value(
        self,
        snapshot: BaseTelemetrySnapshot,
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
    snapshot = _FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=245.1, gear=6)

    assert mapper.get_value(snapshot, "speed") == 245.1
    assert mapper.get_value(snapshot, "gear") == 6


def test_example_sensor_mapper_unknown_key_raises():
    mapper = ExampleSensorMapper()
    snapshot = _FakeSnapshot(lap_distance=0.0, lap_time_ms=0)

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
    snapshot = _FakeSnapshot(lap_distance=0.0, lap_time_ms=0)  # never consulted

    assert mapper.get_value(snapshot, "speed") == 123.4
    assert mapper.get_value(snapshot, "gear") == 3
    assert mapper.get_value(snapshot, "drs") is None


def test_stub_sensor_mapper_missing_key_returns_none():
    mapper = StubSensorMapper({"speed": 100.0})
    snapshot = _FakeSnapshot(lap_distance=0.0, lap_time_ms=0)

    assert mapper.get_value(snapshot, "not_configured") is None


def test_stub_sensor_mapper_returns_injected_dtype():
    mapper = StubSensorMapper({"speed": 100.0}, dtypes={"speed": SensorDtype.FLOAT32})

    assert mapper.get_dtype("speed") == SensorDtype.FLOAT32


def test_stub_sensor_mapper_missing_dtype_raises():
    mapper = StubSensorMapper({"speed": 100.0})

    with pytest.raises(KeyError):
        mapper.get_dtype("speed")

# ----------------------------------------------------------------------------------------------------------------------
# DriverTelemetryRecorder -- normal path (no flashback yet)
# ----------------------------------------------------------------------------------------------------------------------

def _recorder() -> DriverTelemetryRecorder:
    config = TelemetryRecorderConfig(sensors=["speed", "gear"])
    return DriverTelemetryRecorder(driver_index=0, config=config, mapper=ExampleSensorMapper())


def test_recorder_construction_validates_sensor_keys():
    config = TelemetryRecorderConfig(sensors=["speed", "not_a_real_sensor"])

    with pytest.raises(KeyError):
        DriverTelemetryRecorder(driver_index=0, config=config, mapper=ExampleSensorMapper())


def test_recorder_export_before_any_update():
    recorder = _recorder()

    export = recorder.export()

    assert export.driver_index == 0
    assert export.completed_laps == []
    assert export.in_progress_telemetry == {"lap_distance": [], "speed": [], "gear": []}
    assert export.in_progress_num_points == 0
    assert export.in_progress_lap_number == 1  # default label, never told otherwise


def test_recorder_normal_accumulation():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=150.0, gear=4), frame_id=2)
    recorder.update(_FakeSnapshot(lap_distance=20.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=3)

    export = recorder.export()

    assert export.in_progress_telemetry == {
        "lap_distance": [0.0, 10.0, 20.0],
        "speed": [100.0, 150.0, 200.0],
        "gear": [3, 4, 5],
    }
    assert export.in_progress_num_points == 3
    assert export.completed_laps == []


def test_recorder_stationary_update_in_place():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=105.0, gear=3), frame_id=2)  # car stationary

    export = recorder.export()

    assert export.in_progress_telemetry == {"lap_distance": [10.0], "speed": [105.0], "gear": [3]}
    assert export.in_progress_num_points == 1


def test_recorder_lap_distance_decrease_dropped():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=2)  # dropped

    export = recorder.export()

    assert export.in_progress_telemetry == {"lap_distance": [10.0], "speed": [100.0], "gear": [3]}
    assert export.in_progress_num_points == 1


def test_recorder_missing_sample_value_uses_dtype_sentinel():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=None, gear=None), frame_id=1)

    export = recorder.export()

    assert export.in_progress_telemetry["speed"][0] != export.in_progress_telemetry["speed"][0]  # NaN
    assert export.in_progress_telemetry["gear"] == [-1]


def test_recorder_on_lap_change_empty_buffer_guard():
    recorder = _recorder()

    recorder.on_lap_change(sample_lap_metadata(lap_number=1))

    export = recorder.export()
    assert export.completed_laps == []
    assert export.in_progress_lap_number == 1  # untouched -- on_lap_change() discarded silently


def test_recorder_multi_lap():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=150.0, gear=4), frame_id=2)
    lap_1_metadata = sample_lap_metadata(lap_number=1)
    recorder.on_lap_change(lap_1_metadata)

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=3)

    export = recorder.export()

    assert len(export.completed_laps) == 1
    assert export.completed_laps[0].metadata is lap_1_metadata
    assert lap_1_metadata.num_points == 2  # mutated in place by on_lap_change()
    assert export.completed_laps[0].telemetry == {
        "lap_distance": [0.0, 10.0],
        "speed": [100.0, 150.0],
        "gear": [3, 4],
    }
    assert export.in_progress_lap_number == 2  # lap_1_metadata.lap_number + 1
    assert export.in_progress_telemetry == {"lap_distance": [0.0], "speed": [200.0], "gear": [5]}
    assert export.in_progress_num_points == 1


def test_recorder_export_is_non_mutating():
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=2)

    first = recorder.export()
    second = recorder.export()

    assert first == second
