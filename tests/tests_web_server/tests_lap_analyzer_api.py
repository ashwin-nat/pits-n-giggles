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

import dataclasses

import pytest
from pydantic import ValidationError

from apps.web.lap_analyzer_api import (RenameSessionRequest, api_error,
                                       driver_to_api, laps_by_driver_to_api,
                                       resolve_track_length_m, lap_to_api,
                                       session_summary_to_api,
                                       session_to_api,
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
        'trackLengthM': 0.0,
        'sessionSlug': None,
        'sensorManifest': [{'key': "speed", 'label': "Speed", 'unit': "km/h", 'type': "continuous"}],
    }


def test_session_to_api_reports_the_save_viewer_slug():
    assert session_to_api(_entry(), "race-monza")['sessionSlug'] == "race-monza"


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
                    tyre_laps=5, pit_in_lap=False, pit_out_lap=False, ers_harvest_limit_j=4_000_000.0,
                    num_points=100, is_good=True)
    assert lap_to_api(lap, 5000.0) == {
        'lapNumber': 12, 'lapTime': 75340, 'valid': True, 'tyreCompound': "Soft",
        'tyreLaps': 5, 'pitInLap': False, 'pitOutLap': False, 'ersHarvestLimitJ': 4_000_000.0, 'isGood': True,
        'sampleCount': 100, 'startDistanceM': None, 'endDistanceM': None, 'maxGapM': None,
        'complete': False, 'incompleteReason': "not recorded past the line",
    }


def test_lap_to_api_reports_coverage_and_verdict():
    lap = ParsedLap(lap_number=3, lap_time_ms=80000, valid=True, tyre_compound="Soft",
                    tyre_laps=2, pit_in_lap=False, pit_out_lap=False, ers_harvest_limit_j=None,
                    num_points=5000, is_good=False,
                    start_distance_m=2.0, end_distance_m=4379.0, max_gap_m=9.0)
    whole = lap_to_api(lap, 4381.0)
    assert (whole['complete'], whole['incompleteReason']) == (True, None)
    assert (whole['startDistanceM'], whole['endDistanceM'], whole['maxGapM']) == (2.0, 4379.0, 9.0)
    assert lap_to_api(lap, 6000.0)['incompleteReason'] == "first 4380 m only"


def test_track_length_falls_back_to_farthest_timed_lap():
    def _lap(number, time_ms, end):
        return ParsedLap(lap_number=number, lap_time_ms=time_ms, valid=True, tyre_compound="Soft",
                         tyre_laps=1, pit_in_lap=False, pit_out_lap=False, ers_harvest_limit_j=None,
                         num_points=10, is_good=False, start_distance_m=0.0, end_distance_m=end,
                         max_gap_m=1.0)
    entry = dataclasses.replace(_entry(), laps_by_driver={
        0: [_lap(1, 80000, 4380.0), _lap(2, None, 9000.0)], 1: [_lap(1, 81000, 4378.0)]})
    assert resolve_track_length_m(entry) == 4380.0
    assert session_to_api(entry)['trackLengthM'] == 4380.0


def test_track_length_prefers_the_recorded_value():
    entry = _entry()
    entry = dataclasses.replace(entry, session=dataclasses.replace(entry.session, track_length_m=4381))
    assert resolve_track_length_m(entry) == 4381.0
    assert session_to_api(entry)['trackLengthM'] == 4381.0


def test_lap_to_api_out_lap_no_time():
    lap = ParsedLap(lap_number=1, lap_time_ms=None, valid=False, tyre_compound="Medium",
                    tyre_laps=1, pit_in_lap=False, pit_out_lap=True, ers_harvest_limit_j=None,
                    num_points=50, is_good=False)
    result = lap_to_api(lap, 5000.0)
    assert result['lapTime'] is None
    assert result['incompleteReason'] == "no lap time"
    assert result['valid'] is False


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


def _cov_lap(number, time_ms, start, end, valid=True, pit_in=False, pit_out=False, compound="Soft"):
    return ParsedLap(lap_number=number, lap_time_ms=time_ms, valid=valid, tyre_compound=compound,
                     tyre_laps=number, pit_in_lap=pit_in, pit_out_lap=pit_out, ers_harvest_limit_j=None,
                     num_points=100, is_good=False, start_distance_m=start, end_distance_m=end, max_gap_m=3.0)


def _summary_entry(session_type="race"):
    base = _entry()
    session = dataclasses.replace(base.session, session_type=session_type, track_length_m=5000)
    public = ParsedDriver(driver_index=1, name="A", team="T", car_number=1, nationality=None,
                          platform=None, is_telemetry_public=True)
    restricted = dataclasses.replace(public, driver_index=2, name="B", is_telemetry_public=False)
    laps = [
        _cov_lap(1, 95000, 240.0, 4998.0),          # standing start: incomplete (starts late)
        _cov_lap(2, 90000, 1.0, 4998.0),            # eligible, best
        _cov_lap(3, 89000, 1.0, 4998.0, valid=False),
        _cov_lap(4, 88000, 1.0, 4998.0, pit_in=True),
        _cov_lap(5, 85000, 2000.0, 4998.0),         # faster but incomplete (starts late)
    ]
    return dataclasses.replace(base, session=session, drivers=[public, restricted],
                               laps_by_driver={1: laps, 2: []})


def test_session_summary_picks_the_best_eligible_lap_and_the_faster_partial():
    summary = session_summary_to_api(_summary_entry(), "race-save")
    assert summary['sessionSlug'] == "race-save"
    assert summary['trackLengthM'] == 5000.0
    assert summary['completeLapCount'] == 3   # laps 2, 3 and 4 are whole, whatever their flags
    [driver] = summary['drivers']             # restricted driver omitted
    assert driver['best'] == {'lapNumber': 2, 'lapTime': 90000, 'tyreCompound': "Soft"}
    assert driver['fasterIncomplete'] == {
        'lapNumber': 5, 'lapTime': 85000, 'tyreCompound': "Soft", 'reason': "last 3000 m only"}


def test_session_summary_race_lap_one_is_not_a_best_but_other_types_allow_it():
    laps = [_cov_lap(1, 80000, 1.0, 4998.0), _cov_lap(2, 90000, 1.0, 4998.0)]
    race = dataclasses.replace(_summary_entry(), laps_by_driver={1: laps})
    quali = dataclasses.replace(_summary_entry("qualifying"), laps_by_driver={1: laps})
    assert session_summary_to_api(race)['drivers'][0]['best']['lapNumber'] == 2
    assert session_summary_to_api(quali)['drivers'][0]['best']['lapNumber'] == 1


def test_laps_by_driver_to_api_keys_every_driver_by_index():
    result = laps_by_driver_to_api(_summary_entry())
    assert set(result) == {"1", "2"}
    assert [lap['lapNumber'] for lap in result["1"]] == [1, 2, 3, 4, 5]
    assert result["2"] == []
    assert result["1"][0]['complete'] is False
