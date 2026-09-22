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
#
# Tests for lib.pngt.ingest.session_export_manager.SessionExportManager -- a generic
# library class, so (like tests_pngt_ingest.py) this suite has no dependency on
# apps/backend's F1-specific TelemetrySnapshot/F1SensorMapper; it uses its own minimal
# stand-ins instead.

import os
import sys
from dataclasses import dataclass
from typing import Optional

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.pngt import (
    BaseTelemetrySnapshot,
    IngestLapMetadata,
    SensorDtype,
    SensorMapper,
    SessionBest,
    SessionExportManager,
    SessionExportScopeConfig,
    TelemetryRecorderConfig,
)

# ----------------------------------------------------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------------------------------------------------

@dataclass(slots=True)
class _FakeSnapshot(BaseTelemetrySnapshot):
    speed: Optional[float] = None


class _FakeMapper(SensorMapper):
    """Resolves exactly one sensor, "speed" -- enough to exercise recorder construction
    without needing any real (F1-specific) sensor catalog."""

    def get_value(self, snapshot, sensor_key):
        if sensor_key != "speed":
            raise KeyError(sensor_key)
        return snapshot.speed

    def get_dtype(self, sensor_key):
        if sensor_key != "speed":
            raise KeyError(sensor_key)
        return SensorDtype.FLOAT32


def make_snapshot(lap_distance: float, lap_time_ms: int, speed: float = 200.0) -> _FakeSnapshot:
    return _FakeSnapshot(lap_distance=lap_distance, lap_time_ms=lap_time_ms, speed=speed)


def make_lap(lap_number: int, lap_time_ms: int = 90_000, valid: bool = True) -> IngestLapMetadata:
    return IngestLapMetadata(
        lap_number=lap_number,
        lap_time_ms=lap_time_ms,
        valid=valid,
        tyre_compound="Soft",
        tyre_laps=lap_number,
        pit_in_lap=False,
        pit_out_lap=False,
        num_points=0,
    )


@pytest.fixture(name="manager")
def fixture_manager() -> SessionExportManager:
    return SessionExportManager(
        scope_config=SessionExportScopeConfig(),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )


def own_car_scope() -> dict:
    return {"is_telemetry_public": True, "is_player": True, "is_spectating": False}


def other_human_scope() -> dict:
    return {"is_telemetry_public": True, "is_player": False, "is_spectating": False}

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- recorder lifecycle
# ----------------------------------------------------------------------------------------------------------------------

def test_update_creates_recorder_on_first_call(manager: SessionExportManager) -> None:
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    assert 0 in manager._recorders  # pylint: disable=protected-access
    assert manager.export_all().keys() == {0}


def test_update_noop_for_already_discarded_driver(manager: SessionExportManager) -> None:
    manager.apply_scope_update(0, is_telemetry_public=False, is_player=True, is_spectating=False)
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    assert 0 not in manager._recorders  # pylint: disable=protected-access
    assert manager.export_all() == {}


def test_scope_disqualification_before_telemetry_prevents_recorder_creation(manager: SessionExportManager) -> None:
    """Scope facts arriving first must be remembered even with no recorder yet --
    otherwise a restricted driver would get a recorder built for them anyway on first
    telemetry."""
    manager.apply_scope_update(3, is_telemetry_public=False, is_player=False, is_spectating=False)
    manager.update(3, make_snapshot(5.0, 500), frame_id=1)
    manager.update(3, make_snapshot(15.0, 600), frame_id=2)
    assert 3 not in manager._recorders  # pylint: disable=protected-access


def test_scope_disqualification_after_telemetry_drops_recorder(manager: SessionExportManager) -> None:
    manager.update(1, make_snapshot(10.0, 1000), frame_id=1)
    assert 1 in manager._recorders  # pylint: disable=protected-access
    manager.apply_scope_update(1, is_telemetry_public=False, is_player=False, is_spectating=False)
    assert 1 not in manager._recorders  # pylint: disable=protected-access
    assert manager.export_all() == {}


def test_apply_scope_update_does_not_un_discard(manager: SessionExportManager) -> None:
    manager.apply_scope_update(2, is_telemetry_public=False, is_player=True, is_spectating=False)
    manager.apply_scope_update(2, **own_car_scope())
    manager.update(2, make_snapshot(10.0, 1000), frame_id=1)
    assert 2 not in manager._recorders  # pylint: disable=protected-access

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- scope decision table
# ----------------------------------------------------------------------------------------------------------------------

def test_own_car_always_recorded_even_when_other_players_cars_disabled() -> None:
    manager = SessionExportManager(
        scope_config=SessionExportScopeConfig(record_other_players_cars=False),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    manager.apply_scope_update(0, **own_car_scope())
    assert 0 in manager.export_all()


@pytest.mark.parametrize("record_other_players_cars,expected_recorded", [(False, False), (True, True)])
def test_other_human_car_respects_record_other_players_cars(
    record_other_players_cars: bool,
    expected_recorded: bool,
) -> None:
    manager = SessionExportManager(
        scope_config=SessionExportScopeConfig(record_other_players_cars=record_other_players_cars),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )
    manager.update(1, make_snapshot(10.0, 1000), frame_id=1)
    manager.apply_scope_update(1, **other_human_scope())
    assert (1 in manager.export_all()) is expected_recorded


@pytest.mark.parametrize("enabled_in_spectator_mode,expected_recorded", [(False, False), (True, True)])
def test_spectator_mode_gate_applies_regardless_of_is_player(
    enabled_in_spectator_mode: bool,
    expected_recorded: bool,
) -> None:
    manager = SessionExportManager(
        scope_config=SessionExportScopeConfig(enabled_in_spectator_mode=enabled_in_spectator_mode),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )
    manager.update(4, make_snapshot(10.0, 1000), frame_id=1)
    manager.apply_scope_update(4, is_telemetry_public=True, is_player=True, is_spectating=True)
    assert (4 in manager.export_all()) is expected_recorded


def test_restricted_telemetry_discarded_regardless_of_other_flags(manager: SessionExportManager) -> None:
    manager.update(5, make_snapshot(10.0, 1000), frame_id=1)
    manager.apply_scope_update(5, is_telemetry_public=False, is_player=True, is_spectating=False)
    assert 5 not in manager.export_all()

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- on_lap_change routing + session best
# ----------------------------------------------------------------------------------------------------------------------

def test_on_lap_change_noop_without_a_recorder(manager: SessionExportManager) -> None:
    manager.on_lap_change(9, make_lap(1))  # no update() ever called for driver 9
    assert manager.session_best() is None


def test_on_lap_change_noop_for_discarded_driver(manager: SessionExportManager) -> None:
    manager.update(6, make_snapshot(10.0, 1000), frame_id=1)
    manager.apply_scope_update(6, is_telemetry_public=False, is_player=True, is_spectating=False)
    manager.on_lap_change(6, make_lap(1, lap_time_ms=80_000))
    assert manager.session_best() is None


def test_session_best_tracks_fastest_valid_lap_across_drivers(manager: SessionExportManager) -> None:
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    manager.update(1, make_snapshot(10.0, 1000), frame_id=1)

    manager.on_lap_change(0, make_lap(1, lap_time_ms=95_000))
    manager.on_lap_change(1, make_lap(1, lap_time_ms=88_000))
    manager.on_lap_change(0, make_lap(2, lap_time_ms=90_000))

    assert manager.session_best() == SessionBest(driver_index=1, lap_number=1, lap_time_ms=88_000)


def test_session_best_ignores_invalid_laps(manager: SessionExportManager) -> None:
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    manager.on_lap_change(0, make_lap(1, lap_time_ms=50_000, valid=False))
    assert manager.session_best() is None

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- export_all / clear
# ----------------------------------------------------------------------------------------------------------------------

def test_export_all_excludes_discarded_drivers(manager: SessionExportManager) -> None:
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    manager.update(1, make_snapshot(10.0, 1000), frame_id=1)
    manager.apply_scope_update(1, is_telemetry_public=False, is_player=False, is_spectating=False)

    result = manager.export_all()
    assert result.keys() == {0}


def test_clear_resets_to_a_fresh_state(manager: SessionExportManager) -> None:
    manager.update(0, make_snapshot(10.0, 1000), frame_id=1)
    manager.on_lap_change(0, make_lap(1, lap_time_ms=88_000))
    manager.apply_scope_update(1, is_telemetry_public=False, is_player=False, is_spectating=False)

    manager.clear()

    assert manager.export_all() == {}
    assert manager.session_best() is None
    assert manager._recorders == {}  # pylint: disable=protected-access
    assert manager._discarded == set()  # pylint: disable=protected-access

    # behaves like a fresh instance afterward
    manager.update(1, make_snapshot(10.0, 1000), frame_id=1)
    assert 1 in manager.export_all()
