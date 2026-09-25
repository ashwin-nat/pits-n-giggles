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
from typing import Optional

import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.pngt import (BaseTelemetrySnapshot, DriverTelemetryRecorder,
                      LapMetadata, RecordedSensor, SensorConfig, SensorType)

# ----------------------------------------------------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------------------------------------------------

@dataclass(slots=True)
class _FakeSnapshot(BaseTelemetrySnapshot):
    """Test-only stand-in for a real snapshot object -- subclasses BaseTelemetrySnapshot
    the same way a real consumer's snapshot would (see apps/backend/state_mgmt_layer/data_per_driver's own
    TelemetrySnapshot), just with two fake sensor fields instead of ~40 real ones. This
    suite tests the generic recorder, so it has no reason to depend on apps/backend's
    own (F1-specific) TelemetrySnapshot itself."""
    speed: Optional[float] = None
    gear: Optional[int] = None


def sample_lap_metadata(lap_number: int) -> LapMetadata:
    return LapMetadata(
        lap_number=lap_number,
        lap_time_ms=90000,
        valid=True,
        tyre_compound="Soft",
        tyre_laps=lap_number,
        pit_in_lap=False,
        pit_out_lap=False,
    )


def _sensors() -> list[RecordedSensor[_FakeSnapshot]]:
    """Test-only sensor catalog for exercising DriverTelemetryRecorder's buffering/
    flashback/export logic -- a real one (e.g. apps/backend's F1_SENSORS) is
    domain-specific and belongs with whatever code builds the real snapshot."""
    return [
        RecordedSensor(SensorConfig(key="speed", label="Speed", unit="u/s", type=SensorType.CONTINUOUS),
                       lambda s: s.speed),
        RecordedSensor(SensorConfig(key="gear", label="Gear", unit="", type=SensorType.DISCRETE),
                       lambda s: s.gear),
    ]


def _recorder() -> DriverTelemetryRecorder:
    return DriverTelemetryRecorder(driver_index=0, sensors=_sensors())

# ----------------------------------------------------------------------------------------------------------------------
# Construction
# ----------------------------------------------------------------------------------------------------------------------

def test_recorder_rejects_duplicate_sensor_keys():
    sensors = _sensors() + [_sensors()[0]]
    with pytest.raises(ValueError):
        DriverTelemetryRecorder(driver_index=0, sensors=sensors)

# ----------------------------------------------------------------------------------------------------------------------
# DriverTelemetryRecorder -- normal path (no flashback yet)
# ----------------------------------------------------------------------------------------------------------------------

def test_recorder_export_before_any_update():
    recorder = _recorder()

    export = recorder.export()

    assert export.driver_index == 0
    assert export.completed_laps == []
    assert export.in_progress_lap is None


def test_recorder_normal_accumulation():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=150.0, gear=4), frame_id=2)
    recorder.update(_FakeSnapshot(lap_distance=20.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=3)

    export = recorder.export()

    assert export.completed_laps == []
    assert export.in_progress_lap.telemetry == {
        "lap_distance": [0.0, 10.0, 20.0],
        "lap_time_ms": [0, 0, 0],
        "speed": [100.0, 150.0, 200.0],
        "gear": [3, 4, 5],
    }


def test_recorder_stationary_update_in_place():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=105.0, gear=3), frame_id=2)  # car stationary

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [10.0], "lap_time_ms": [0], "speed": [105.0], "gear": [3],
    }


def test_recorder_lap_distance_decrease_dropped():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=2)  # dropped

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [10.0], "lap_time_ms": [0], "speed": [100.0], "gear": [3],
    }


def test_recorder_missing_sample_value_is_nan():
    # Every sensor is stored float32 now -- NaN is the only missing-value marker,
    # for continuous and discrete sensors alike.
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=None, gear=None), frame_id=1)

    telemetry = recorder.export().in_progress_lap.telemetry
    assert telemetry["speed"][0] != telemetry["speed"][0]  # NaN
    assert telemetry["gear"][0] != telemetry["gear"][0]  # NaN


def test_recorder_on_lap_change_empty_buffer_guard():
    recorder = _recorder()

    recorder.on_lap_change(sample_lap_metadata(lap_number=1))

    export = recorder.export()
    assert export.completed_laps == []
    assert export.in_progress_lap is None  # on_lap_change() discarded silently, nothing buffered since


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
    assert export.completed_laps[0].telemetry == {
        "lap_distance": [0.0, 10.0],
        "lap_time_ms": [0, 0],
        "speed": [100.0, 150.0],
        "gear": [3, 4],
    }
    assert export.in_progress_lap.metadata.lap_number == 2  # lap_1_metadata.lap_number + 1
    assert export.in_progress_lap.telemetry == {
        "lap_distance": [0.0], "lap_time_ms": [0], "speed": [200.0], "gear": [5],
    }


def test_recorder_export_is_non_mutating():
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1)
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=2)

    first = recorder.export()
    second = recorder.export()

    assert first == second

# ----------------------------------------------------------------------------------------------------------------------
# DriverTelemetryRecorder -- flashback detection + rollback
# ----------------------------------------------------------------------------------------------------------------------

def test_recorder_flashback_case_a_truncates_within_current_lap():
    """Target frame_id (3) falls within the current lap's own buffer (frames 1-5) --
    truncate to it, then process the flashback packet itself as a normal append against
    the now-truncated last sample."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=1), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=110.0, gear=2), frame_id=2)
    recorder.update(_FakeSnapshot(lap_distance=20.0, lap_time_ms=0, speed=120.0, gear=3), frame_id=3)
    recorder.update(_FakeSnapshot(lap_distance=30.0, lap_time_ms=0, speed=130.0, gear=4), frame_id=4)
    recorder.update(_FakeSnapshot(lap_distance=40.0, lap_time_ms=0, speed=140.0, gear=5), frame_id=5)

    # Flashback to frame 3: buffers truncate to [1, 2, 3], then this packet appends as frame 3 again.
    recorder.update(_FakeSnapshot(lap_distance=25.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=3)

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [0.0, 10.0, 20.0, 25.0],
        "lap_time_ms": [0, 0, 0, 0],
        "speed": [100.0, 110.0, 120.0, 999.0],
        "gear": [1, 2, 3, 9],
    }
    assert export.completed_laps == []


def test_recorder_flashback_case_b_restores_completed_lap_then_reallows_finalising_it():
    """Target frame_id (1) predates the current (second) lap entirely -- pop the last
    completed lap, truncate it to the target, restore it as the new current buffer, then
    process the flashback packet itself as a normal append. Once re-finalised via a
    second on_lap_change(), it becomes a genuinely new completed lap -- the original
    LapMetadata object is gone, discarded by the rollback."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=1), frame_id=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=110.0, gear=2), frame_id=2)
    original_lap_1 = sample_lap_metadata(lap_number=1)
    recorder.on_lap_change(original_lap_1)  # current_lap_number becomes 2

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=3), frame_id=3)
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=210.0, gear=4), frame_id=4)

    # Flashback to frame 1, before lap 2 ever started: lap 1 is popped and truncated to
    # frame 1, restored as the current buffer, then this packet appends as frame 1 again.
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=1)

    export = recorder.export()
    assert export.completed_laps == []  # lap 1 was popped, not restored to completed_laps
    assert export.in_progress_lap.metadata.lap_number == 1  # the restored lap's own number, not 2
    assert export.in_progress_lap.telemetry == {
        "lap_distance": [0.0, 5.0],
        "lap_time_ms": [0, 0],
        "speed": [100.0, 999.0],
        "gear": [1, 9],
    }

    # Re-finalising with a fresh LapMetadata proves the restored data is treated as a
    # genuinely new lap, independent of the original (discarded) object.
    redone_lap_1 = sample_lap_metadata(lap_number=1)
    recorder.on_lap_change(redone_lap_1)
    final_export = recorder.export()

    assert redone_lap_1 is not original_lap_1
    assert len(final_export.completed_laps) == 1
    assert final_export.completed_laps[0].metadata is redone_lap_1
    assert final_export.in_progress_lap is None  # nothing buffered yet for lap 2


def test_recorder_flashback_case_b_with_no_earlier_lap_clears_buffers():
    """Target frame_id predates even the first sample ever recorded, with no completed
    lap to restore from -- buffers are cleared, not crashed, and recording continues
    normally from the flashback packet itself."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=1.0, gear=1), frame_id=5)

    recorder.update(_FakeSnapshot(lap_distance=3.0, lap_time_ms=0, speed=2.0, gear=2), frame_id=2)

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [3.0], "lap_time_ms": [0], "speed": [2.0], "gear": [2],
    }
    assert export.in_progress_lap.metadata.lap_number == 1
