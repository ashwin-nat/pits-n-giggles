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

"""Pure mapping functions from lib/pngt's read-side DTOs (snake_case, on-disk field
names) to the lap-analyzer REST API's JSON shapes (camelCase, per the API spec's Data
Models section). No I/O, no Quart -- kept separate from web_server.py's route
handlers so the mapping itself is trivially unit-testable.

Mirrors apps/lap-analyzer/src/providers/LocalFileProvider.ts's own mapping field for
field (including titleCaseSessionType's transform) -- that's what "no behavioural
difference between LocalFileProvider and RemoteApiProvider" (this phase's exit
criterion) actually depends on matching.

One deliberate divergence from the original API spec: `Driver.isAi` is dropped
entirely rather than populated. The .pngt format has no is_ai field to source it
from -- it was removed project-wide (see the `remove is_ai` commit) because there's no
reliable signal to record it from in the first place. apps/lap-analyzer's own
Driver type (types/api.ts) already reflects this: it has no isAi field either.

Response shapes are plain dicts, built directly in the API's camelCase -- there's
no wire-format translation to buy back with a model here. Pydantic is used only
where it's actually validating untrusted input: RenameSessionRequest, the one
request body this API takes.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from lib.pngt import (LapCoverage, LapVerdict, ParsedDriver, ParsedLap,
                      SensorConfig, judge_lap_coverage)
from lib.track_segments_classifier.types import BaseSegmentInfo

from .pngt_discovery import PngtSessionEntry

# -------------------------------------- MODELS ------------------------------------------------------------------------

class RenameSessionRequest(BaseModel):
    """PATCH /sessions/:sessionId/name's request body. `min_length`/`max_length`
    cover the 400 INVALID_NAME cases the API spec calls "empty string or exceeds
    character limit"; the extra validator catches a whitespace-only name, which
    min_length=1 alone wouldn't (a single space has length 1)."""
    name: str = Field(min_length=1, max_length=255)

    @field_validator('name')
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('name must not be blank')
        return v

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def title_case_session_type(raw: str) -> str:
    """'time_trial' -> 'Time Trial', 'race' -> 'Race'. session_type is an intentionally
    open string (see file format spec -- new sim session types must not require a
    format change); this only capitalizes it, it never validates against a fixed set.
    """
    words = [w for w in raw.replace('_', ' ').split() if w]
    return ' '.join(w[:1].upper() + w[1:] for w in words)


def api_error(code: str, message: str) -> Dict[str, Any]:
    return {'error': {'code': code, 'message': message}}


def _sensor_to_api(sensor: SensorConfig) -> Dict[str, Any]:
    d = {'key': sensor.key, 'label': sensor.label, 'unit': sensor.unit, 'type': sensor.type.value}
    if sensor.range is not None:
        d['range'] = list(sensor.range)
    return d


def _track_length_m(entry: PngtSessionEntry) -> float:
    """The recorded track length; 0.0 when the game never sent one, which leaves only
    the late-start and gap checks of the completeness rule in effect."""
    return float(entry.session.track_length_m or 0)


def session_to_api(entry: PngtSessionEntry, save_viewer_slug: Optional[str] = None) -> Dict[str, Any]:
    session = entry.session
    session_best = None if session.session_best is None else {
        'driverIndex': session.session_best.driver_index,
        'lapNumber': session.session_best.lap_number,
        'lapTimeMs': session.session_best.lap_time_ms,
    }
    return {
        'id': entry.slug,
        'name': session.session_name,
        'trackId': session.track.id,
        'trackName': session.track.name,
        'date': session.timestamp,
        'type': title_case_session_type(session.session_type),
        'appVersion': session.app_version,
        'gameYear': session.game_year,
        'formula': session.formula,
        'gameVersion': session.game_version,
        'sessionBest': session_best,
        'trackLengthM': _track_length_m(entry),
        'sessionSlug': save_viewer_slug,  # the save-viewer session this recording belongs to
        'playerIndex': session.player_index,
        'sectorStartsM': None if session.sector_starts_m is None else list(session.sector_starts_m),
        'ersMaxCapacityJ': session.ers_max_capacity_j,
        'sensorManifest': [_sensor_to_api(s) for s in entry.sensors if s.should_display],
    }


def driver_laps_to_api(entry: PngtSessionEntry, driver_index: int) -> List[Dict[str, Any]]:
    track_length_m = _track_length_m(entry)
    return [lap_to_api(lap, track_length_m) for lap in entry.laps_by_driver.get(driver_index, [])]


def laps_by_driver_to_api(entry: PngtSessionEntry) -> Dict[str, List[Dict[str, Any]]]:
    """Every driver's laps in one response, keyed by driver index (JSON keys are strings)."""
    return {str(index): driver_laps_to_api(entry, index) for index in entry.laps_by_driver}


def session_summary_to_api(entry: PngtSessionEntry, save_viewer_slug: Optional[str] = None) -> Dict[str, Any]:
    """One row of the recording list: the session's identity plus, per driver, the best
    eligible lap and any faster lap that was not captured whole. Eligible means complete,
    valid, timed, not a pit lap, and not a race's standing-start lap 1."""
    session_type = title_case_session_type(entry.session.session_type)
    is_race = session_type.startswith('Race')
    track_length_m = _track_length_m(entry)
    complete_count = 0
    drivers = []
    for driver in entry.drivers:
        if not driver.is_telemetry_public:
            continue
        best: Optional[ParsedLap] = None
        partial: Optional[ParsedLap] = None
        partial_reason = None
        for lap in entry.laps_by_driver.get(driver.driver_index, []):
            verdict = _lap_verdict(lap, track_length_m)
            complete_count += verdict.complete
            if (verdict.complete and lap.valid and lap.lap_time_ms and not lap.pit_in_lap
                    and not lap.pit_out_lap and not (is_race and lap.lap_number == 1)):
                if best is None or lap.lap_time_ms < best.lap_time_ms:
                    best = lap
            elif (not verdict.complete and lap.valid and lap.lap_time_ms
                    and (partial is None or lap.lap_time_ms < partial.lap_time_ms)):
                partial, partial_reason = lap, verdict.reason
        drivers.append({
            'index': driver.driver_index,
            'name': driver.name,
            'team': driver.team,
            'best': None if best is None else _lap_summary(best),
            'fasterIncomplete': None if partial is None or (best and partial.lap_time_ms >= best.lap_time_ms)
            else {**_lap_summary(partial), 'reason': partial_reason or 'partial trace'},
        })
    return {
        'id': entry.slug,
        'type': session_type,
        'trackName': entry.session.track.name,
        'date': entry.session.timestamp,
        'formula': entry.session.formula,
        'gameYear': entry.session.game_year,
        'trackLengthM': track_length_m,
        'sessionSlug': save_viewer_slug,
        'playerIndex': entry.session.player_index,
        'completeLapCount': complete_count,
        'drivers': drivers,
    }


def _lap_summary(lap: ParsedLap) -> Dict[str, Any]:
    return {'lapNumber': lap.lap_number, 'lapTime': lap.lap_time_ms, 'tyreCompound': lap.tyre_compound}


def driver_to_api(driver: ParsedDriver) -> Dict[str, Any]:
    return {
        'index': driver.driver_index,
        'name': driver.name,
        'team': driver.team,
        'carNumber': driver.car_number,
        'nationality': driver.nationality,
        'platform': driver.platform,
        'telemetrySettings': 'Public' if driver.is_telemetry_public else 'Restricted',
    }


def _lap_verdict(lap: ParsedLap, track_length_m: float) -> LapVerdict:
    return judge_lap_coverage(
        lap.lap_time_ms, LapCoverage(lap.start_distance_m, lap.end_distance_m, lap.max_gap_m),
        track_length_m)


def lap_to_api(lap: ParsedLap, track_length_m: float) -> Dict[str, Any]:
    verdict = _lap_verdict(lap, track_length_m)
    return {
        'lapNumber': lap.lap_number,
        'lapTime': lap.lap_time_ms,
        'valid': lap.valid,
        'tyreCompound': lap.tyre_compound,
        'tyreLaps': lap.tyre_laps,
        'pitInLap': lap.pit_in_lap,
        'pitOutLap': lap.pit_out_lap,
        'ersHarvestLimitJ': lap.ers_harvest_limit_j,
        'isGood': lap.is_good,
        'sampleCount': lap.num_points,
        'startDistanceM': lap.start_distance_m,
        'endDistanceM': lap.end_distance_m,
        'maxGapM': lap.max_gap_m,
        'complete': verdict.complete,
        'incompleteReason': verdict.reason,
        'sectorEndsMs': None if lap.sector_ends_ms is None else list(lap.sector_ends_ms),
    }


def track_section_to_api(segment: BaseSegmentInfo) -> Dict[str, Any]:
    """Maps one lib/track_segments_classifier segment to the API's TrackSection shape.

    Mirrors apps/lap-analyzer/src/lib/segments.ts's toSections() field for
    field, including corner_numbers derivation -- one-element list for a
    plain corner, the full tuple for a complex corner, empty for a straight.
    No "Full Lap"/"Sector N" synthesis here; see that module's own comment on
    why sector/track-length data is a separate, not-yet-served concept.
    """
    if segment.type == "corner":
        corner_numbers = [segment.corner_number]
    elif segment.type == "complex_corner":
        corner_numbers = list(segment.corner_numbers)
    else:
        corner_numbers = []
    return {
        'label': segment.name,
        'distanceStart': segment.start_m,
        'distanceEnd': segment.end_m,
        'type': segment.type,
        'cornerNumbers': corner_numbers,
    }
