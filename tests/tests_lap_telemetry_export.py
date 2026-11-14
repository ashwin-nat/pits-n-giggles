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
# Tests for the app side of the lap telemetry export: apps.backend.state_mgmt_layer.lap_telemetry_export
# (sensor selection and filtering) and the session facts stored with a recording. This is app/business logic,
# not lib/pngt, so its tests live here. Lap events are in tests_session_state/.

import os
import sys
from types import SimpleNamespace

import allure
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import DataPerDriver
from apps.backend.state_mgmt_layer.data_per_driver.telemetry_recorder.telemetry_recorder import F1_SENSORS
from apps.backend.state_mgmt_layer.lap_telemetry_export import _filter_export, selected_sensors
from lib.config import LapAnalyzerSensorSettings, LapAnalyzerSettings
from lib.pngt import CompletedLap, DriverExportData, LapMetadata

pytestmark = allure.epic("Lap telemetry export")

# ----------------------------------------------------------------------------------------------------------------------
# F1_SENSORS <-> LapAnalyzerSensorSettings mapping
# ----------------------------------------------------------------------------------------------------------------------

@allure.feature("Sensor mapping")
def test_sensor_keys_match_config_fields():
    assert F1_SENSORS.keys() == LapAnalyzerSensorSettings.model_fields.keys()


@allure.feature("Sensor mapping")
def test_pngt_sensor_keys_unique():
    keys = [s.config.key for s in F1_SENSORS.values()]
    assert len(keys) == len(set(keys))


@allure.feature("Sensor mapping")
@pytest.mark.parametrize("field", list(F1_SENSORS))
def test_manifest_label_comes_from_own_config_field(field):
    assert F1_SENSORS[field].config.label == LapAnalyzerSensorSettings.model_fields[field].description

# ----------------------------------------------------------------------------------------------------------------------
# selected_sensors()
# ----------------------------------------------------------------------------------------------------------------------

DEFAULT_KEYS = {"throttle", "brake", "steering", "speed", "gear", "engine_rpm",
                "ers.deploy_mode", "ers.store_energy"}


def _all_off() -> dict:
    return {f: False for f in LapAnalyzerSensorSettings.model_fields}


@allure.feature("Sensor selection")
def test_selected_sensors_disabled_is_empty():
    assert selected_sensors(LapAnalyzerSettings(enable=False)) == []


@allure.feature("Sensor selection")
def test_selected_sensors_defaults():
    assert {s.key for s in selected_sensors(LapAnalyzerSettings())} == DEFAULT_KEYS


@allure.feature("Sensor selection")
def test_selected_sensors_all_off_is_empty():
    assert selected_sensors(LapAnalyzerSettings(Sensors=_all_off())) == []

# ----------------------------------------------------------------------------------------------------------------------
# _filter_export()
# ----------------------------------------------------------------------------------------------------------------------

def _lap(number: int, *, in_progress: bool = False) -> CompletedLap:
    meta = LapMetadata(lap_number=number, lap_time_ms=None if in_progress else 90000, valid=not in_progress,
                       tyre_compound="soft", tyre_laps=1, pit_in_lap=False, pit_out_lap=False,
                       ers_harvest_limit_j=None)
    return CompletedLap(meta, {"lap_distance": [0, 1, 2], "lap_time_ms": [0, 10, 20],
                               "throttle": [1, 2, 3], "brake": [4, 5, 6], "ers.deploy_mode": [0, 1, 2]})


@allure.feature("Export filter")
def test_filter_export_keeps_mandatory_plus_selected():
    data = DriverExportData(driver_index=3, completed_laps=[_lap(1), _lap(2)],
                            in_progress_lap=_lap(3, in_progress=True))
    out = _filter_export(data, {"throttle"})
    assert out.driver_index == 3
    for lap in [*out.completed_laps, out.in_progress_lap]:
        assert set(lap.telemetry) == {"lap_distance", "lap_time_ms", "throttle"}
        assert all(len(v) == 3 for v in lap.telemetry.values())
    assert out.in_progress_lap.metadata.lap_number == 3


@allure.feature("Export filter")
def test_filter_export_without_in_progress_lap():
    out = _filter_export(DriverExportData(driver_index=0, completed_laps=[_lap(1)]), {"brake"})
    assert out.in_progress_lap is None
    assert set(out.completed_laps[0].telemetry) == {"lap_distance", "lap_time_ms", "brake"}


# -------------------------------------- session facts stored with the recording ---------------------------------------

from apps.backend.state_mgmt_layer.lap_telemetry_export import (
    _sector_starts_m, build_lap_telemetry_write_args)
from lib.f1_types import PacketSessionData
from pathlib import Path


@allure.feature("Session facts")
def test_sector_starts_m():
    packet = SimpleNamespace(m_sector2LapDistanceStart=1897.8, m_sector3LapDistanceStart=3726.9)
    assert _sector_starts_m(packet) == (1897.8, 3726.9)


@allure.feature("Session facts")
def test_sector_starts_m_without_a_session_packet():
    assert _sector_starts_m(None) is None


@allure.feature("Session facts")
@pytest.mark.parametrize("s1,s1_min,s2,s2_min,lap,expected", [
    (35769, 0, 32537, 0, 98464, (35769, 68306)),
    (5000, 1, 32537, 0, 140000, (65000, 97537)),   # a sector over a minute long
    (0, 0, 32537, 0, 98464, None),                 # missing split
    (55000, 0, 40000, 0, 60000, None),             # a partial lap copies a sector into its lap time
])
def test_sector_ends_ms(s1, s1_min, s2, s2_min, lap, expected):
    hist_lap = SimpleNamespace(m_sector1TimeInMS=s1, m_sector1TimeMinutes=s1_min,
                               m_sector2TimeInMS=s2, m_sector2TimeMinutes=s2_min, m_lapTimeInMS=lap)
    assert DataPerDriver._sectorEndsMs(hist_lap) == expected


@allure.feature("Session facts")
@pytest.mark.parametrize("formula,expected", [
    (PacketSessionData.FormulaType.F1_MODERN, 4_000_000.0),
    (PacketSessionData.FormulaType.F2, None),     # F2 cars have no ERS
    (None, None),                                  # formula not known yet
])
def test_ers_capacity_is_only_recorded_for_f1(formula, expected):
    state = SimpleNamespace(
        m_driver_data=[], m_player_index=3, m_png_version="1.0", m_game_version="1.0",
        m_session_info=SimpleNamespace(
            m_session_uid=1, m_session_type="Race", m_game_year=26, m_formula=formula, m_track=None,
            m_track_len=5810, m_packet_session=None))
    _, session, _, _, _ = build_lap_telemetry_write_args(state, Path("x.pngt"), LapAnalyzerSettings())
    assert session.ers_max_capacity_j == expected
    assert session.player_index == 3
