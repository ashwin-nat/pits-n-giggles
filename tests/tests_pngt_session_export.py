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
# Tests for apps.backend.state_mgmt_layer.pngt_export.in_export_scope() -- the
# "which drivers get exported" policy. This is app/business logic (not lib/pngt,
# which has no scope concept at all), so its tests live here rather than under
# tests_pngt*.py.

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.state_mgmt_layer.data_per_driver.telemetry_recorder.telemetry_recorder import F1_SENSORS
from apps.backend.state_mgmt_layer.session_state import SessionState
from apps.backend.state_mgmt_layer.pngt_export import (_filter_export, in_export_scope,
                                                       selected_sensors)
from lib.config import LapAnalyzerSensorSettings, LapAnalyzerSettings
from lib.pngt import CompletedLap, DriverExportData, LapMetadata

# ----------------------------------------------------------------------------------------------------------------------
# in_export_scope() decision table
# ----------------------------------------------------------------------------------------------------------------------

def test_restricted_telemetry_never_in_scope():
    assert in_export_scope(
        is_public=False, is_player=True, is_spectating=False, spectator_mode=True, other_players=True,
    ) is False


def test_own_car_always_in_scope_even_when_other_players_cars_disabled():
    assert in_export_scope(
        is_public=True, is_player=True, is_spectating=False, spectator_mode=False, other_players=False,
    ) is True


@pytest.mark.parametrize("other_players,expected", [(False, False), (True, True)])
def test_other_human_car_respects_other_players(other_players, expected):
    assert in_export_scope(
        is_public=True, is_player=False, is_spectating=False, spectator_mode=False, other_players=other_players,
    ) is expected


@pytest.mark.parametrize("spectator_mode,expected", [(False, False), (True, True)])
def test_spectator_mode_gate_applies_regardless_of_is_player(spectator_mode, expected):
    # No "own car" while spectating, so is_player=True must not bypass the gate.
    assert in_export_scope(
        is_public=True, is_player=True, is_spectating=True, spectator_mode=spectator_mode, other_players=True,
    ) is expected

# ----------------------------------------------------------------------------------------------------------------------
# F1_SENSORS <-> LapAnalyzerSensorSettings mapping
# ----------------------------------------------------------------------------------------------------------------------

def test_sensor_keys_match_config_fields():
    assert F1_SENSORS.keys() == LapAnalyzerSensorSettings.model_fields.keys()


def test_pngt_sensor_keys_unique():
    keys = [s.config.key for s in F1_SENSORS.values()]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("field", list(F1_SENSORS))
def test_manifest_label_comes_from_own_config_field(field):
    assert F1_SENSORS[field].config.label == LapAnalyzerSensorSettings.model_fields[field].description

# ----------------------------------------------------------------------------------------------------------------------
# selected_sensors()
# ----------------------------------------------------------------------------------------------------------------------

BEGINNER_KEYS = {"throttle", "brake", "steering", "speed", "gear", "engine_rpm"}


def _all_off() -> dict:
    return {f: False for f in LapAnalyzerSensorSettings.model_fields}


def test_selected_sensors_disabled_is_empty():
    assert selected_sensors(LapAnalyzerSettings(enable=False)) == []


def test_selected_sensors_defaults_are_beginner_six():
    assert {s.key for s in selected_sensors(LapAnalyzerSettings())} == BEGINNER_KEYS


def test_selected_sensors_all_off_is_empty():
    assert selected_sensors(LapAnalyzerSettings(Sensors=_all_off())) == []

# ----------------------------------------------------------------------------------------------------------------------
# _filter_export()
# ----------------------------------------------------------------------------------------------------------------------

def _lap(number: int, *, in_progress: bool = False) -> CompletedLap:
    meta = LapMetadata(lap_number=number, lap_time_ms=None if in_progress else 90000, valid=not in_progress,
                       tyre_compound="soft", tyre_laps=1, pit_in_lap=False, pit_out_lap=False)
    return CompletedLap(meta, {"lap_distance": [0, 1, 2], "lap_time_ms": [0, 10, 20],
                               "throttle": [1, 2, 3], "brake": [4, 5, 6], "ers.deploy_mode": [0, 1, 2]})


def test_filter_export_keeps_mandatory_plus_selected():
    data = DriverExportData(driver_index=3, completed_laps=[_lap(1), _lap(2)],
                            in_progress_lap=_lap(3, in_progress=True))
    out = _filter_export(data, {"throttle"})
    assert out.driver_index == 3
    for lap in [*out.completed_laps, out.in_progress_lap]:
        assert set(lap.telemetry) == {"lap_distance", "lap_time_ms", "throttle"}
        assert all(len(v) == 3 for v in lap.telemetry.values())
    assert out.in_progress_lap.metadata.lap_number == 3


def test_filter_export_without_in_progress_lap():
    out = _filter_export(DriverExportData(driver_index=0, completed_laps=[_lap(1)]), {"brake"})
    assert out.in_progress_lap is None
    assert set(out.completed_laps[0].telemetry) == {"lap_distance", "lap_time_ms", "brake"}

# ----------------------------------------------------------------------------------------------------------------------
# SessionState.updateLapAnalyzerSettings()
# ----------------------------------------------------------------------------------------------------------------------

def _fake_state(enable: bool):
    driver = SimpleNamespace(m_tel_rec=MagicMock())
    return SimpleNamespace(m_lap_analyzer_settings=LapAnalyzerSettings(enable=enable),
                           m_driver_data=[driver, None]), driver


@pytest.mark.parametrize("old,new,discards", [(True, False, True), (False, True, False),
                                              (True, True, False), (False, False, False)])
def test_update_settings_discards_in_progress_lap_only_when_disabling(old, new, discards):
    state, driver = _fake_state(old)
    new_settings = LapAnalyzerSettings(enable=new)
    SessionState.updateLapAnalyzerSettings(state, new_settings)
    assert state.m_lap_analyzer_settings is new_settings
    assert driver.m_tel_rec.discard_in_progress_lap.called is discards
