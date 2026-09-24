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

import numpy as np
import pytest
from pydantic import ValidationError

from apps.web.lap_analyzer_api import (RenameSessionRequest, api_error,
                                       driver_to_api, lap_to_api,
                                       session_to_api,
                                       telemetry_points_to_api,
                                       title_case_session_type,
                                       track_section_to_api)
from apps.web.pngt_discovery import PngtSessionEntry
from lib.pngt import (ParsedDriver, ParsedLap, ParsedSessionMetadata,
                      SensorConfig, SensorType, SessionBest, TrackInfo)
from lib.track_segments_classifier.types import (ComplexCornerSegmentInfo,
                                                 CornerSegmentInfo,
                                                 StraightSegmentInfo)


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
    session = ParsedSessionMetadata(
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
    driver = ParsedDriver(driver_index=1, name="VERSTAPPEN", team="RED BULL RACING",
                          car_number=1, nationality="NED", platform="PC", is_telemetry_public=True)
    assert driver_to_api(driver) == {
        'index': 1, 'name': "VERSTAPPEN", 'team': "RED BULL RACING", 'carNumber': 1,
        'nationality': "NED", 'platform': "PC", 'telemetrySettings': "Public",
    }
    assert 'isAi' not in driver_to_api(driver)


def test_driver_to_api_restricted_telemetry():
    driver = ParsedDriver(driver_index=16, name="LECLERC", team="FERRARI",
                          car_number=16, nationality="MON", platform=None, is_telemetry_public=False)
    result = driver_to_api(driver)
    assert result['telemetrySettings'] == "Restricted"
    assert result['platform'] is None


def test_lap_to_api_completed_lap():
    lap = ParsedLap(lap_number=12, lap_time_ms=75340, valid=True, tyre_compound="Soft",
                    tyre_laps=5, pit_in_lap=False, pit_out_lap=False, num_points=100, is_good=True)
    assert lap_to_api(lap) == {
        'lapNumber': 12, 'lapTime': 75340, 'valid': True, 'tyreCompound': "Soft",
        'tyreLaps': 5, 'pitInLap': False, 'pitOutLap': False, 'isGood': True,
    }


def test_lap_to_api_out_lap_no_time():
    lap = ParsedLap(lap_number=1, lap_time_ms=None, valid=False, tyre_compound="Medium",
                    tyre_laps=1, pit_in_lap=False, pit_out_lap=True, num_points=50, is_good=False)
    result = lap_to_api(lap)
    assert result['lapTime'] is None
    assert result['valid'] is False


def test_telemetry_points_maps_lap_distance_and_requested_sensors():
    lap_distance = np.array([0.0, 1.7, 3.3], dtype=np.float32)
    arrays = {
        'lap_distance': lap_distance,
        'speed': np.array([112.3, 114.1, 116.8], dtype=np.float32),
        'gear': np.array([4, 4, 5], dtype=np.int8),
    }
    points = telemetry_points_to_api(lap_distance, arrays, ['speed', 'gear'])

    assert len(points) == 3
    assert points[0]['lapDistance'] == pytest.approx(0.0)
    assert points[1]['speed'] == pytest.approx(114.1, rel=1e-4)
    assert points[2]['gear'] == 5
    # numpy scalars must not leak through -- Quart's default JSON provider can't
    # serialize them.
    assert isinstance(points[0]['lapDistance'], float)
    assert isinstance(points[2]['gear'], int)


def test_telemetry_points_only_includes_requested_sensors():
    lap_distance = np.array([0.0, 1.0], dtype=np.float32)
    arrays = {
        'lap_distance': lap_distance,
        'speed': np.array([100.0, 110.0], dtype=np.float32),
        'throttle': np.array([0.5, 0.6], dtype=np.float32),
    }
    points = telemetry_points_to_api(lap_distance, arrays, ['speed'])

    assert set(points[0].keys()) == {'lapDistance', 'speed'}


def test_telemetry_points_omits_sensor_missing_from_this_laps_arrays():
    """A sensor requested (valid per the session manifest) but absent from this
    particular lap's own npz -- e.g. an older recording -- is omitted per point,
    matching LocalFileProvider.ts's getTelemetry(), not set to null."""
    lap_distance = np.array([0.0, 1.0], dtype=np.float32)
    arrays = {'lap_distance': lap_distance}
    points = telemetry_points_to_api(lap_distance, arrays, ['speed'])

    assert points[0] == {'lapDistance': 0.0}
    assert 'speed' not in points[0]


def test_telemetry_points_float32_nan_becomes_null():
    """float32's own missing-sample sentinel (NaN) must become JSON null -- literal
    NaN has no representation in standard JSON and JS's JSON.parse rejects it."""
    lap_distance = np.array([0.0, 100.0], dtype=np.float32)
    arrays = {'lap_distance': lap_distance, 'speed': np.array([100.0, np.nan], dtype=np.float32)}
    points = telemetry_points_to_api(lap_distance, arrays, ['speed'])

    assert points[1]['speed'] is None


def test_telemetry_points_int_missing_sentinel_passed_through():
    """The integer dtypes' missing-sample sentinel (-1) is NOT converted to null --
    it's indistinguishable from a genuine value (e.g. reverse gear) at this layer,
    and LocalFileProvider.ts makes the same choice."""
    lap_distance = np.array([0.0, 100.0], dtype=np.float32)
    arrays = {'lap_distance': lap_distance, 'gear': np.array([1, -1], dtype=np.int8)}
    points = telemetry_points_to_api(lap_distance, arrays, ['gear'])

    assert points[1]['gear'] == -1


def test_track_section_straight():
    seg = StraightSegmentInfo(name="Kemmel Straight", start_m=890, end_m=2100)
    assert track_section_to_api(seg) == {
        'label': "Kemmel Straight", 'distanceStart': 890, 'distanceEnd': 2100,
        'type': "straight", 'cornerNumbers': [],
    }


def test_track_section_corner():
    seg = CornerSegmentInfo(name="La Source", start_m=0, end_m=210, corner_number=1)
    result = track_section_to_api(seg)
    assert result['type'] == "corner"
    assert result['cornerNumbers'] == [1]


def test_track_section_complex_corner():
    seg = ComplexCornerSegmentInfo(name="Bus Stop", start_m=6500, end_m=7004, corner_numbers=(18, 19))
    result = track_section_to_api(seg)
    assert result['type'] == "complex_corner"
    assert result['cornerNumbers'] == [18, 19]


def test_track_section_unnamed_corner_uses_empty_label():
    """Corners can have an empty name in the source data (see file format spec) --
    the API's label is whatever's there, not synthesized from the corner number."""
    seg = CornerSegmentInfo(name="", start_m=311, end_m=480, corner_number=1)
    assert track_section_to_api(seg)['label'] == ""


def test_rename_session_request_accepts_valid_name():
    request = RenameSessionRequest.model_validate({"name": "League Race Night"})
    assert request.name == "League Race Night"


def test_rename_session_request_rejects_empty_name():
    with pytest.raises(ValidationError):
        RenameSessionRequest.model_validate({"name": ""})


def test_rename_session_request_rejects_whitespace_only_name():
    """min_length=1 alone wouldn't catch this -- a single space has length 1."""
    with pytest.raises(ValidationError):
        RenameSessionRequest.model_validate({"name": "   "})


def test_rename_session_request_rejects_over_length_name():
    with pytest.raises(ValidationError):
        RenameSessionRequest.model_validate({"name": "x" * 256})


def test_rename_session_request_accepts_name_at_length_limit():
    request = RenameSessionRequest.model_validate({"name": "x" * 255})
    assert len(request.name) == 255


def test_rename_session_request_rejects_non_dict_body():
    """A malformed/missing JSON body (server.request.get_json(silent=True) returns
    None) must fail validation, not raise an unrelated AttributeError."""
    with pytest.raises(ValidationError):
        RenameSessionRequest.model_validate(None)


def test_api_error_envelope_shape():
    result = api_error('SESSION_NOT_FOUND', 'Unknown session id: foo')
    assert result == {
        'error': {'code': 'SESSION_NOT_FOUND', 'message': 'Unknown session id: foo'},
    }
