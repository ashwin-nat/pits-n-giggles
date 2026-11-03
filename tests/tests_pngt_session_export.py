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
# Tests for the app side of the .pngt export: apps.backend.state_mgmt_layer.pngt_export
# (sensor selection and filtering) and the lap events SessionState reports to DataPerDriver.
# This is app/business logic, not lib/pngt, so its tests live here.

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import DataPerDriver
from apps.backend.state_mgmt_layer.data_per_driver.telemetry_recorder.telemetry_recorder import F1_SENSORS
from apps.backend.state_mgmt_layer.session_state import SessionState
from apps.backend.state_mgmt_layer.pngt_export import _filter_export, selected_sensors
from lib.config import LapAnalyzerSensorSettings, LapAnalyzerSettings
from lib.f1_types import LapData
from lib.pngt import CompletedLap, DriverExportData, LapMetadata

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

DEFAULT_KEYS = {"throttle", "brake", "steering", "speed", "gear", "engine_rpm",
                "ers.deploy_mode", "ers.store_energy"}


def _all_off() -> dict:
    return {f: False for f in LapAnalyzerSensorSettings.model_fields}


def test_selected_sensors_disabled_is_empty():
    assert selected_sensors(LapAnalyzerSettings(enable=False)) == []


def test_selected_sensors_defaults():
    assert {s.key for s in selected_sensors(LapAnalyzerSettings())} == DEFAULT_KEYS


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

# ----------------------------------------------------------------------------------------------------------------------
# SessionState lap management -- lap changes, flashbacks, and boundaries the sim's lap number doesn't show
# ----------------------------------------------------------------------------------------------------------------------

GARAGE, FLYING, IN_LAP, OUT_LAP, ON_TRACK = (LapData.DriverStatus.IN_GARAGE, LapData.DriverStatus.FLYING_LAP,
                                             LapData.DriverStatus.IN_LAP, LapData.DriverStatus.OUT_LAP,
                                             LapData.DriverStatus.ON_TRACK)


def _session(*, race: bool = False, flashback: bool = False):
    session_type = SimpleNamespace(isRaceTypeSession=lambda: race, isTimeTrialTypeSession=lambda: False)
    state = SimpleNamespace(
        m_session_info=SimpleNamespace(m_session_type=session_type, m_track_len=5810, curr_weather=None),
        m_flashback_occurred=flashback, m_logger=MagicMock(), m_pkt_fmt=2025)
    return state


def _lap_data(status, lap, distance):
    return SimpleNamespace(m_driverStatus=status, m_currentLapNum=lap, m_lapDistance=distance)


def _feed_boundaries(packets, **session_kwargs):
    """Feed (status, lap, raw distance) packets the way processLapDataUpdate() does. Returns the driver mock."""
    state = _session(**session_kwargs)
    driver = MagicMock()
    driver.m_packet_copies.m_packet_lap_data = None
    for packet in packets:
        lap_data = _lap_data(*packet)
        SessionState._handleLapBoundaries(state, driver, lap_data)
        driver.m_packet_copies.m_packet_lap_data = lap_data  # updateLapDataPacketCopy()
    return driver


def test_garage_entry_reported_once_including_the_first_packet():
    driver = _feed_boundaries([(GARAGE, 1, 228.7), (GARAGE, 1, -5581.2), (OUT_LAP, 1, -5542.9)])
    assert driver.onGarageEntry.call_count == 1


@pytest.mark.parametrize("packets", [
    [(OUT_LAP, 1, -5542.9), (OUT_LAP, 1, -1.2), (FLYING, 1, 0.6)],   # first run: counts up to 0
    [(OUT_LAP, 2, 222.0), (OUT_LAP, 2, 5809.7), (FLYING, 2, 1.0)],   # later run: wraps at the line
])
def test_out_lap_to_flying_lap_starts_the_lap(packets):
    assert _feed_boundaries(packets).onLapStart.call_count == 1


@pytest.mark.parametrize("packets", [
    [(FLYING, 1, 5809.0), (FLYING, 2, 0.6)],                       # normal lap change: onLapChange()'s job
    [(FLYING, 1, 5809.0), (FLYING, 2, 0.6), (IN_LAP, 2, 3.0)],     # in-lap starts just after the lap change
    [(IN_LAP, 2, 5809.8), (IN_LAP, 2, 0.1)],                       # in-lap crossing the line in the pit lane
    [(OUT_LAP, 1, -5581.1), (OUT_LAP, 1, -1590.7)],                # 'Flying lap' spawn into S3
    [(GARAGE, 1, -5581.2), (OUT_LAP, 1, -5542.9)],                 # leaving the garage
])
def test_no_lap_start_without_out_lap_to_flying_lap(packets):
    assert not _feed_boundaries(packets).onLapStart.called


def test_races_are_left_alone():
    # The cool-down lap after the flag wraps without a lap change; restarting there would lose the last lap
    driver = _feed_boundaries([(ON_TRACK, 5, 5809.9), (ON_TRACK, 5, 1.2), (GARAGE, 5, 228.7)], race=True)
    assert not driver.onLapStart.called and not driver.onGarageEntry.called


def test_landing_packet_is_not_a_line_crossing():
    driver = _feed_boundaries([(OUT_LAP, 1, -1.2), (FLYING, 1, 30.0)], flashback=True)
    assert not driver.onLapStart.called


def _lap_change(current_lap, new_lap, *, flashback=False):
    state = _session(flashback=flashback)
    driver = MagicMock()
    driver.shouldCaptureZerothLapSnapshot.return_value = False
    driver.m_lap_info.m_current_lap = current_lap
    SessionState._handleLapChangeLogic(state, driver, _lap_data(FLYING, new_lap, 5749.6))
    return state, driver


def test_lap_increment_completes_the_previous_lap():
    _, driver = _lap_change(2, 3)
    driver.onLapChange.assert_called_once_with(old_lap_number=2)
    assert not driver.onFlashback.called
    assert driver.m_lap_info.m_current_lap == 3


@pytest.mark.parametrize("current_lap,new_lap", [(3, 2), (3, 3)])
def test_flashback_is_reported_whether_or_not_it_crossed_the_line(current_lap, new_lap):
    state, driver = _lap_change(current_lap, new_lap, flashback=True)
    driver.onFlashback.assert_called_once_with(new_lap, 5749.6, state.m_session_info.m_session_type)
    assert not driver.onLapChange.called


def test_lap_count_going_back_without_a_flashback_changes_nothing_but_the_lap():
    _, driver = _lap_change(5, 1)
    assert not driver.onLapChange.called and not driver.onFlashback.called
    assert driver.m_lap_info.m_current_lap == 1

# ----------------------------------------------------------------------------------------------------------------------
# DataPerDriver.onFlashback() -- fans one flashback out to every per-driver consumer
# ----------------------------------------------------------------------------------------------------------------------

def _rewind(current_lap, landing_lap, *, time_trial=False):
    driver = SimpleNamespace(m_lap_info=SimpleNamespace(m_current_lap=current_lap), _handleFlashBack=MagicMock(),
                             m_delta_mgr=MagicMock(), m_tel_rec=MagicMock())
    session_type = SimpleNamespace(isTimeTrialTypeSession=lambda: time_trial)
    DataPerDriver.onFlashback(driver, landing_lap, 5749.6, session_type)
    return driver


def test_flashback_within_lap_trims_delta_and_recorder_only():
    driver = _rewind(3, 3)
    assert not driver._handleFlashBack.called
    driver.m_delta_mgr.handle_flashback.assert_called_once_with(3, 5749.6)
    driver.m_tel_rec.on_flashback.assert_called_once_with(3, 5749.6)


def test_flashback_across_the_line_also_drops_the_redone_laps():
    driver = _rewind(3, 2)
    driver._handleFlashBack.assert_called_once_with(2)
    driver.m_tel_rec.on_flashback.assert_called_once_with(2, 5749.6)


def test_flashback_in_time_trial_skips_the_delta():
    driver = _rewind(3, 3, time_trial=True)
    assert not driver.m_delta_mgr.handle_flashback.called
    driver.m_tel_rec.on_flashback.assert_called_once_with(3, 5749.6)
