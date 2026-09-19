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
# pylint: skip-file

"""apps.web.lap_analyzer_api: pure lib/pngt DTO -> API JSON mapping.

title_case_session_type and the field mappings are pinned to match
apps/lap-analyzer/src/providers/LocalFileProvider.ts's own mapping exactly -- that
equivalence is what Phase 6's exit criterion ("no behavioural difference between
LocalFileProvider and RemoteApiProvider") actually depends on.
"""

import pytest

from apps.web.lap_analyzer_api import (driver_to_api, lap_to_api,
                                       session_to_api,
                                       title_case_session_type)
from apps.web.pngt_discovery import PngtSessionEntry
from lib.pngt import (DriverRecord, LapMetadata, SensorConfig, SensorType,
                      SessionBest, SessionMetadata, TrackInfo)


@pytest.mark.parametrize("raw,expected", [
    ("race", "Race"),
    ("time_trial", "Time Trial"),
    ("qualifying", "Qualifying"),
    ("", ""),
    ("one_shot_qualifying_shootout", "One Shot Qualifying Shootout"),
])
def test_title_case_session_type(raw, expected):
    assert title_case_session_type(raw) == expected


def _entry(session_best=SessionBest(driver_index=1, lap_number=2, lap_time_ms=90000)):
    session = SessionMetadata(
        session_uid=1, session_name="Test Session", session_type="time_trial",
        app_version="1.4.2", game_year=2026, formula="F1", game_version="1.05",
        timestamp="2024-06-01T14:32:00Z", track=TrackInfo(id=10, name="Spa-Francorchamps"),
        laps_count=2, session_best=session_best,
    )
    sensors = [SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)]
    return PngtSessionEntry(
        slug="test-session", rel_path="test.pngt", session=session,
        drivers=[], sensors=sensors, laps_by_driver={},
    )


def test_session_to_api_maps_all_fields():
    result = session_to_api(_entry())
    assert result == {
        'id': "test-session",
        'name': "Test Session",
        'trackId': 10,
        'trackName': "Spa-Francorchamps",
        'date': "2024-06-01T14:32:00Z",
        'type': "Time Trial",
        'appVersion': "1.4.2",
        'gameYear': 2026,
        'formula': "F1",
        'gameVersion': "1.05",
        'sessionBest': {'driverIndex': 1, 'lapNumber': 2, 'lapTimeMs': 90000},
        'sensorManifest': [{'key': "speed", 'label': "Speed", 'unit': "km/h", 'type': "continuous"}],
    }


def test_session_to_api_null_session_best():
    result = session_to_api(_entry(session_best=None))
    assert result['sessionBest'] is None


def test_driver_to_api_public_telemetry():
    driver = DriverRecord(driver_index=1, name="VERSTAPPEN", team="RED BULL RACING",
                          car_number=1, nationality="NED", platform="PC", is_telemetry_public=True)
    assert driver_to_api(driver) == {
        'index': 1, 'name': "VERSTAPPEN", 'team': "RED BULL RACING", 'carNumber': 1,
        'nationality': "NED", 'platform': "PC", 'telemetrySettings': "Public",
    }
    assert 'isAi' not in driver_to_api(driver)


def test_driver_to_api_restricted_telemetry():
    driver = DriverRecord(driver_index=16, name="LECLERC", team="FERRARI",
                          car_number=16, nationality="MON", platform=None, is_telemetry_public=False)
    result = driver_to_api(driver)
    assert result['telemetrySettings'] == "Restricted"
    assert result['platform'] is None


def test_lap_to_api_completed_lap():
    lap = LapMetadata(lap_number=12, lap_time_ms=75340, valid=True, tyre_compound="Soft",
                      tyre_laps=5, pit_in_lap=False, pit_out_lap=False, num_points=100, is_good=True)
    assert lap_to_api(lap) == {
        'lapNumber': 12, 'lapTime': 75340, 'valid': True, 'tyreCompound': "Soft",
        'tyreLaps': 5, 'pitInLap': False, 'pitOutLap': False, 'isGood': True,
    }


def test_lap_to_api_out_lap_no_time():
    lap = LapMetadata(lap_number=1, lap_time_ms=None, valid=False, tyre_compound="Medium",
                      tyre_laps=1, pit_in_lap=False, pit_out_lap=True, num_points=50, is_good=False)
    result = lap_to_api(lap)
    assert result['lapTime'] is None
    assert result['valid'] is False
