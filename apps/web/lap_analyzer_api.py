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

import math
from typing import Any, Dict, List

import numpy as np
from pydantic import BaseModel, Field, field_validator

from lib.pngt import ParsedDriver, ParsedLap, SensorConfig
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


def session_to_api(entry: PngtSessionEntry) -> Dict[str, Any]:
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
        'sensorManifest': [_sensor_to_api(s) for s in entry.sensors],
    }


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


def lap_to_api(lap: ParsedLap) -> Dict[str, Any]:
    return {
        'lapNumber': lap.lap_number,
        'lapTime': lap.lap_time_ms,
        'valid': lap.valid,
        'tyreCompound': lap.tyre_compound,
        'tyreLaps': lap.tyre_laps,
        'pitInLap': lap.pit_in_lap,
        'pitOutLap': lap.pit_out_lap,
        'isGood': lap.is_good,
    }


def _to_json_value(value: Any) -> Any:
    """One raw npz sample -> a JSON-safe Python value.

    Every sensor array is float32; NaN is its only missing-sample marker, and it
    becomes None here since literal NaN has no representation in standard JSON and
    would fail to parse on the browser side (Quart's default JSON provider emits the
    bare `NaN` token, which JS's own `JSON.parse` rejects). A real value that happens
    to be -1 (e.g. gear == -1 for reverse) is passed through unchanged.
    """
    native = value.item() if hasattr(value, 'item') else value
    if isinstance(native, float) and math.isnan(native):
        return None
    return native


def telemetry_points_to_api(
    lap_distance: np.ndarray,
    sensor_arrays: Dict[str, np.ndarray],
    sensors: List[str],
) -> List[Dict[str, Any]]:
    """Build the API's TelemetryPoint[] shape from one lap's raw npz arrays.

    Mirrors LocalFileProvider.ts's getTelemetry(): a requested sensor key entirely
    absent from `sensor_arrays` (an older or narrower recording than the session's
    current manifest) is simply omitted from every point, not set to null -- null is
    reserved for a *present* array's own missing-sample value (see _to_json_value).

    lap_time_ms is included unconditionally, like lap_distance -- it's a mandatory
    pngt array (lib/pngt/recorder.py's BaseTelemetrySnapshot), not something the
    caller opts into via `sensors`. The chart area uses it to derive the delta trace
    against a reference lap regardless of which sensors the user has selected.
    """
    points: List[Dict[str, Any]] = []
    lap_time_ms = sensor_arrays.get('lap_time_ms')
    for i, distance in enumerate(lap_distance):
        point: Dict[str, Any] = {'lapDistance': _to_json_value(distance)}
        if lap_time_ms is not None:
            point['lap_time_ms'] = _to_json_value(lap_time_ms[i])
        for sensor in sensors:
            array = sensor_arrays.get(sensor)
            if array is not None:
                point[sensor] = _to_json_value(array[i])
        points.append(point)
    return points


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
