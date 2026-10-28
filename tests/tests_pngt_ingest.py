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

import itertools
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
        ers_harvest_limit_j=None,
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


_FRAME_IDS = itertools.count()  # frame IDs only go back on a flashback


def _drive(recorder: DriverTelemetryRecorder, distances, *, lap: int, t0: int = 0, step_ms: int = 100) -> None:
    """Feed one sample per distance, the lap timer counting up from t0."""
    for i, distance in enumerate(distances):
        recorder.update(_FakeSnapshot(lap_distance=distance, lap_time_ms=t0 + i * step_ms, speed=1.0, gear=1),
                        frame_id=next(_FRAME_IDS), lap_number=lap)


def _land(recorder: DriverTelemetryRecorder, distance: float, *, lap: int, t: int = 0) -> None:
    """A flashback, then the packet the car landed in."""
    recorder.on_flashback(lap, distance)
    recorder.update(_FakeSnapshot(lap_distance=distance, lap_time_ms=t, speed=1.0, gear=1), frame_id=0, lap_number=lap)


def _distances(lap) -> list:
    return lap.telemetry["lap_distance"]

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

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=150.0, gear=4), frame_id=2, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=20.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=3, lap_number=1)

    export = recorder.export()

    assert export.completed_laps == []
    assert export.in_progress_lap.telemetry == {
        "lap_distance": [0.0, 10.0, 20.0],
        "lap_time_ms": [0, 0, 0],
        "speed": [100.0, 150.0, 200.0],
        "gear": [3, 4, 5],
    }


def test_recorder_first_update_seeds_lap_number():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=1.0, gear=1), frame_id=1, lap_number=4)

    assert recorder.export().in_progress_lap.metadata.lap_number == 4


def test_recorder_stationary_update_in_place():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=105.0, gear=3), frame_id=2, lap_number=1)  # car stationary

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [10.0], "lap_time_ms": [0], "speed": [105.0], "gear": [3],
    }


def test_recorder_lap_distance_decrease_dropped():
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=2, lap_number=1)  # dropped

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [10.0], "lap_time_ms": [0], "speed": [100.0], "gear": [3],
    }


def test_recorder_missing_sample_value_is_nan():
    # Every sensor is stored float32 now -- NaN is the only missing-value marker,
    # for continuous and discrete sensors alike.
    recorder = _recorder()

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=None, gear=None), frame_id=1, lap_number=1)

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

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=150.0, gear=4), frame_id=2, lap_number=1)
    lap_1_metadata = sample_lap_metadata(lap_number=1)
    recorder.on_lap_change(lap_1_metadata)

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=3, lap_number=2)

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
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=3), frame_id=1, lap_number=1)
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=5), frame_id=2, lap_number=2)

    first = recorder.export()
    second = recorder.export()

    assert first == second

# ----------------------------------------------------------------------------------------------------------------------
# DriverTelemetryRecorder -- flashback rollback
# ----------------------------------------------------------------------------------------------------------------------

def test_recorder_flashback_before_any_update_is_ignored():
    recorder = _recorder()

    recorder.on_flashback(1, 100.0)

    assert recorder.export().in_progress_lap is None


def test_recorder_flashback_case_a_truncates_within_current_lap():
    """Landed at 25 within the current lap -- truncate to the samples before it, then
    process the landing packet itself as a normal append against the now-truncated last sample."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=1), frame_id=1, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=110.0, gear=2), frame_id=2, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=20.0, lap_time_ms=0, speed=120.0, gear=3), frame_id=3, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=30.0, lap_time_ms=0, speed=130.0, gear=4), frame_id=4, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=40.0, lap_time_ms=0, speed=140.0, gear=5), frame_id=5, lap_number=1)

    # Flashback landing at 25: buffers truncate to [0, 10, 20], then this packet appends.
    recorder.on_flashback(1, 25.0)
    recorder.update(_FakeSnapshot(lap_distance=25.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=3, lap_number=1)

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [0.0, 10.0, 20.0, 25.0],
        "lap_time_ms": [0, 0, 0, 0],
        "speed": [100.0, 110.0, 120.0, 999.0],
        "gear": [1, 2, 3, 9],
    }
    assert export.completed_laps == []


def test_recorder_flashback_keeps_everything_before_the_landing_point():
    """The sim can resume a rewind well past its own target frame (seen: 154 m later).
    Truncating at the landing distance leaves no hole."""
    recorder = _recorder()
    _drive(recorder, [3900.0, 4000.7, 4100.0, 4154.0, 4300.0, 4511.0], lap=1)

    _land(recorder, 4154.3, lap=1, t=70494)

    assert _distances(recorder.export().in_progress_lap) == [3900.0, 4000.7, 4100.0, 4154.0, 4154.3]


def test_recorder_repeated_rewinds_to_just_after_the_line():
    recorder = _recorder()
    _drive(recorder, [1.1, 20.0, 39.0, 300.0, 545.0], lap=1)
    for _ in range(3):
        _land(recorder, 42.2, lap=1, t=609)
        _drive(recorder, [200.0, 450.0], lap=1, t0=700)

    assert _distances(recorder.export().in_progress_lap) == [1.1, 20.0, 39.0, 42.2, 200.0, 450.0]


def test_recorder_flashback_case_b_restores_completed_lap_then_reallows_finalising_it():
    """Landed in lap 1 from the current (second) lap -- pop the last completed lap,
    truncate it to the landing distance, restore it as the new current buffer, then
    process the landing packet itself as a normal append. Once re-finalised via a
    second on_lap_change(), it becomes a genuinely new completed lap -- the original
    LapMetadata object is gone, discarded by the rollback."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=100.0, gear=1), frame_id=1, lap_number=1)
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=110.0, gear=2), frame_id=2, lap_number=1)
    original_lap_1 = sample_lap_metadata(lap_number=1)
    recorder.on_lap_change(original_lap_1)  # current_lap_number becomes 2

    recorder.update(_FakeSnapshot(lap_distance=0.0, lap_time_ms=0, speed=200.0, gear=3), frame_id=3, lap_number=2)
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=210.0, gear=4), frame_id=4, lap_number=2)

    # Flashback landing at 5 in lap 1: lap 1 is popped and truncated to [0], restored as
    # the current buffer, then this packet appends.
    recorder.on_flashback(1, 5.0)
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=0, speed=999.0, gear=9), frame_id=1, lap_number=1)

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


def test_recorder_flashback_case_b_into_unstored_lap_carries_on_from_landing():
    recorder = _recorder()
    _drive(recorder, [3000.0, 5800.0], lap=1)
    recorder.discard_in_progress_lap()
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))  # lap 1 not stored
    _drive(recorder, [1.0, 80.0], lap=2)

    _land(recorder, 5750.0, lap=1, t=94000)
    _drive(recorder, [5800.0], lap=1, t0=95000)
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))

    export = recorder.export()
    assert [_distances(lap) for lap in export.completed_laps] == [[5750.0, 5800.0]]
    assert export.in_progress_lap is None


def test_recorder_flashback_before_first_sample_restarts_lap():
    """Landed before even the first sample recorded -- buffers are cleared, not crashed,
    and recording continues normally from the landing packet itself."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=10.0, lap_time_ms=0, speed=1.0, gear=1), frame_id=5, lap_number=1)

    recorder.on_flashback(1, 3.0)
    recorder.update(_FakeSnapshot(lap_distance=3.0, lap_time_ms=0, speed=2.0, gear=2), frame_id=2, lap_number=1)

    export = recorder.export()

    assert export.in_progress_lap.telemetry == {
        "lap_distance": [3.0], "lap_time_ms": [0], "speed": [2.0], "gear": [2],
    }
    assert export.in_progress_lap.metadata.lap_number == 1

# ----------------------------------------------------------------------------------------------------------------------
# DriverTelemetryRecorder -- laps that end without a lap change, and partial laps
# ----------------------------------------------------------------------------------------------------------------------

def test_recorder_discard_at_the_line_drops_out_lap_and_records_flying_lap():
    """A later quali run: the out lap has positive distances and the flying lap keeps its
    lap number, so without a discard at the line every flying-lap sample would be below the
    out lap's last distance and get dropped."""
    recorder = _recorder()
    _drive(recorder, [222.0, 3000.0, 5809.7], lap=2)  # out lap, timer stopped
    recorder.discard_in_progress_lap()
    _drive(recorder, [1.0, 2900.0, 5809.8], lap=2)
    recorder.on_lap_change(sample_lap_metadata(lap_number=2))

    export = recorder.export()
    assert len(export.completed_laps) == 1
    assert export.completed_laps[0].metadata.lap_number == 2
    assert _distances(export.completed_laps[0]) == [1.0, 2900.0, 5809.8]


def test_recorder_lap_first_seen_mid_way_is_stored_as_recorded():
    """Whether a trace covers the whole lap is for the consumer to judge, from its distances."""
    recorder = _recorder()
    _drive(recorder, [3000.0, 4000.0], lap=3, t0=40000)
    assert _distances(recorder.export().in_progress_lap) == [3000.0, 4000.0]

    recorder.on_lap_change(sample_lap_metadata(lap_number=3))
    _drive(recorder, [1.0, 2000.0], lap=4, t0=16)
    recorder.on_lap_change(sample_lap_metadata(lap_number=4))

    export = recorder.export()
    assert [lap.metadata.lap_number for lap in export.completed_laps] == [3, 4]
    assert _distances(export.completed_laps[0]) == [3000.0, 4000.0]


def test_recorder_discard_in_progress_lap_keeps_completed_laps_and_restarts_cleanly():
    """A pause in updates must not splice two recording periods into one lap."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=1.0, lap_time_ms=10, speed=1.0, gear=1), frame_id=1, lap_number=1)
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))
    recorder.update(_FakeSnapshot(lap_distance=1.0, lap_time_ms=10, speed=2.0, gear=2), frame_id=2, lap_number=2)
    recorder.update(_FakeSnapshot(lap_distance=2.0, lap_time_ms=20, speed=3.0, gear=3), frame_id=3, lap_number=2)

    recorder.discard_in_progress_lap()
    assert recorder.export().in_progress_lap is None
    assert len(recorder.export().completed_laps) == 1

    recorder.update(_FakeSnapshot(lap_distance=50.0, lap_time_ms=500, speed=9.0, gear=4), frame_id=100, lap_number=2)
    export = recorder.export()
    assert export.in_progress_lap.telemetry == {
        "lap_distance": [50.0], "lap_time_ms": [500], "speed": [9.0], "gear": [4],
    }
    assert export.in_progress_lap.metadata.lap_number == 2

def test_recorder_lap_resumed_after_discard_is_stored_from_the_resume_point():
    """Only the samples after a discard are stored for that lap -- never both recording periods."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=1.0, lap_time_ms=10, speed=1.0, gear=1), frame_id=1, lap_number=1)
    recorder.discard_in_progress_lap()
    recorder.update(_FakeSnapshot(lap_distance=50.0, lap_time_ms=500, speed=9.0, gear=4), frame_id=100, lap_number=1)

    recorder.on_lap_change(sample_lap_metadata(lap_number=1))
    recorder.update(_FakeSnapshot(lap_distance=1.0, lap_time_ms=10, speed=2.0, gear=2), frame_id=200, lap_number=2)
    recorder.on_lap_change(sample_lap_metadata(lap_number=2))
    export = recorder.export()
    assert [_distances(lap) for lap in export.completed_laps] == [[50.0], [1.0]]


def test_recorder_lap_change_with_empty_buffers_still_advances_lap_number():
    """Recording paused across a lap boundary: the resumed lap must carry the sim's lap number."""
    recorder = _recorder()
    recorder.update(_FakeSnapshot(lap_distance=1.0, lap_time_ms=10, speed=1.0, gear=1), frame_id=1, lap_number=1)
    recorder.on_lap_change(sample_lap_metadata(lap_number=1))
    recorder.on_lap_change(sample_lap_metadata(lap_number=2))  # no samples recorded during lap 2
    recorder.update(_FakeSnapshot(lap_distance=5.0, lap_time_ms=50, speed=2.0, gear=2), frame_id=9, lap_number=3)
    export = recorder.export()
    assert len(export.completed_laps) == 1
    assert export.in_progress_lap.metadata.lap_number == 3
