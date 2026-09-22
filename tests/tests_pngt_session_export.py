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
    DriverExportCandidate,
    DriverRecord,
    IngestCompletedLap,
    IngestDriverExportData,
    IngestLapMetadata,
    SensorConfig,
    SensorDtype,
    SensorMapper,
    SensorType,
    SessionBest,
    SessionExportManager,
    SessionExportScopeConfig,
    SessionMetadata,
    TelemetryRecorderConfig,
    TrackInfo,
    read_driver_laps,
    read_lap_telemetry,
    read_session,
)

# ----------------------------------------------------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------------------------------------------------

@dataclass(slots=True)
class _FakeSnapshot(BaseTelemetrySnapshot):
    speed: Optional[float] = None


class _FakeMapper(SensorMapper):
    """Resolves exactly one sensor, "speed" -- enough to exercise aggregation and
    manifest-building without needing any real (F1-specific) sensor catalog."""

    def get_value(self, snapshot, sensor_key):
        if sensor_key != "speed":
            raise KeyError(sensor_key)
        return snapshot.speed

    def get_dtype(self, sensor_key):
        if sensor_key != "speed":
            raise KeyError(sensor_key)
        return SensorDtype.FLOAT32

    def sensor_config(self, sensor_key):
        if sensor_key != "speed":
            raise KeyError(sensor_key)
        return SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)


def make_ingest_export(driver_index: int, lap_number: int, lap_time_ms: int, valid: bool = True) -> IngestDriverExportData:
    lap = IngestCompletedLap(
        metadata=IngestLapMetadata(
            lap_number=lap_number,
            lap_time_ms=lap_time_ms,
            valid=valid,
            tyre_compound="Soft",
            tyre_laps=lap_number,
            pit_in_lap=False,
            pit_out_lap=False,
            num_points=2,
        ),
        telemetry={"lap_distance": [0.0, 100.0], "lap_time_ms": [0, 1000], "speed": [50.0, 150.0]},
    )
    return IngestDriverExportData(
        driver_index=driver_index,
        completed_laps=[lap],
        in_progress_lap_number=lap_number + 1,
        in_progress_telemetry={},
        in_progress_num_points=0,
    )


@pytest.fixture(name="manager")
def fixture_manager() -> SessionExportManager:
    return SessionExportManager(
        scope_config=SessionExportScopeConfig(),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )


def own_car_scope() -> dict:
    return {"is_telemetry_public": True, "is_player": True}


def other_human_scope() -> dict:
    return {"is_telemetry_public": True, "is_player": False}

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- in_scope() decision table
# ----------------------------------------------------------------------------------------------------------------------

def test_own_car_always_in_scope_even_when_other_players_cars_disabled() -> None:
    manager = SessionExportManager(
        scope_config=SessionExportScopeConfig(record_other_players_cars=False),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )
    assert manager.in_scope(**own_car_scope(), is_spectating=False) is True


@pytest.mark.parametrize("record_other_players_cars,expected", [(False, False), (True, True)])
def test_other_human_car_respects_record_other_players_cars(record_other_players_cars: bool, expected: bool) -> None:
    manager = SessionExportManager(
        scope_config=SessionExportScopeConfig(record_other_players_cars=record_other_players_cars),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )
    assert manager.in_scope(**other_human_scope(), is_spectating=False) is expected


@pytest.mark.parametrize("enabled_in_spectator_mode,expected", [(False, False), (True, True)])
def test_spectator_mode_gate_applies_regardless_of_is_player(enabled_in_spectator_mode: bool, expected: bool) -> None:
    manager = SessionExportManager(
        scope_config=SessionExportScopeConfig(enabled_in_spectator_mode=enabled_in_spectator_mode),
        recorder_config=TelemetryRecorderConfig(sensors=("speed",)),
        mapper=_FakeMapper(),
    )
    assert manager.in_scope(is_telemetry_public=True, is_player=True, is_spectating=True) is expected


def test_restricted_telemetry_never_in_scope(manager: SessionExportManager) -> None:
    assert manager.in_scope(is_telemetry_public=False, is_player=True, is_spectating=False) is False

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- export_scoped()
# ----------------------------------------------------------------------------------------------------------------------

def test_export_scoped_includes_only_in_scope_drivers(manager: SessionExportManager) -> None:
    candidates = [
        DriverExportCandidate(0, lambda: make_ingest_export(0, 1, 90_000), **own_car_scope()),
        DriverExportCandidate(1, lambda: make_ingest_export(1, 1, 91_000), is_telemetry_public=False, is_player=False),
    ]
    result = manager.export_scoped(candidates, is_spectating=False)
    assert result.keys() == {0}
    assert result[0].driver_index == 0


def test_export_scoped_does_not_call_export_fn_for_out_of_scope_candidates(manager: SessionExportManager) -> None:
    calls = []

    def tracked_export():
        calls.append(1)
        return make_ingest_export(1, 1, 90_000)

    candidates = [DriverExportCandidate(1, tracked_export, is_telemetry_public=False, is_player=False)]
    manager.export_scoped(candidates, is_spectating=False)

    assert calls == []


def test_export_scoped_empty_candidates_returns_empty_dict(manager: SessionExportManager) -> None:
    assert manager.export_scoped([], is_spectating=False) == {}

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- compute_session_best()
# ----------------------------------------------------------------------------------------------------------------------

def test_compute_session_best_picks_fastest_valid_lap_across_drivers(manager: SessionExportManager) -> None:
    driver_exports = {
        0: make_ingest_export(0, 1, 95_000),
        1: make_ingest_export(1, 1, 88_000),
    }
    assert manager.compute_session_best(driver_exports) == SessionBest(driver_index=1, lap_number=1, lap_time_ms=88_000)


def test_compute_session_best_ignores_invalid_laps(manager: SessionExportManager) -> None:
    driver_exports = {0: make_ingest_export(0, 1, 50_000, valid=False)}
    assert manager.compute_session_best(driver_exports) is None


def test_compute_session_best_empty_input_returns_none(manager: SessionExportManager) -> None:
    assert manager.compute_session_best({}) is None

# ----------------------------------------------------------------------------------------------------------------------
# Tests -- write_pngt() (aggregation output -> real .pngt file, round trip)
# ----------------------------------------------------------------------------------------------------------------------

def test_write_pngt_round_trips(manager: SessionExportManager, tmp_path) -> None:
    driver_exports = {0: make_ingest_export(0, 1, 88_500)}
    session = SessionMetadata(
        session_uid=42, session_name="Test", session_type="Race", app_version="1.0.0",
        game_year=2025, formula="F1", game_version="1.30", timestamp="2026-09-23T00:00:00Z",
        track=TrackInfo(id=10, name="Spa"), laps_count=1,
        session_best=manager.compute_session_best(driver_exports),
    )
    drivers = [
        DriverRecord(0, "Driver Zero", "Team A", 1, None, None, is_telemetry_public=True),
        DriverRecord(1, "Driver One", "Team B", 2, None, None, is_telemetry_public=False),
    ]

    dest_path = manager.write_pngt(tmp_path / "session.pngt", session, drivers, driver_exports)

    assert dest_path.exists()
    parsed = read_session(dest_path)
    assert parsed.session.session_uid == 42
    assert parsed.session.session_best.lap_time_ms == 88_500
    assert {d.driver_index for d in parsed.drivers} == {0, 1}

    laps = read_driver_laps(dest_path, driver_index=0)
    assert [lap.lap_number for lap in laps] == [1]
    assert read_driver_laps(dest_path, driver_index=1) == []  # restricted, no folder at all

    telemetry = read_lap_telemetry(dest_path, driver_index=0, lap_number=1)
    assert list(telemetry["speed"]) == pytest.approx([50.0, 150.0])
