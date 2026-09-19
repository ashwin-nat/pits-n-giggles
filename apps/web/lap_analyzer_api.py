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
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict

from lib.pngt import DriverRecord, LapMetadata, SensorConfig

from .pngt_discovery import PngtSessionEntry

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def title_case_session_type(raw: str) -> str:
    """'time_trial' -> 'Time Trial', 'race' -> 'Race'. session_type is an intentionally
    open string (see file format spec -- new sim session types must not require a
    format change); this only capitalizes it, it never validates against a fixed set.
    """
    words = [w for w in raw.replace('_', ' ').split() if w]
    return ' '.join(w[:1].upper() + w[1:] for w in words)


def _sensor_to_api(sensor: SensorConfig) -> Dict[str, Any]:
    return {
        'key': sensor.key,
        'label': sensor.label,
        'unit': sensor.unit,
        'type': sensor.type.value,
    }


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


def driver_to_api(driver: DriverRecord) -> Dict[str, Any]:
    return {
        'index': driver.driver_index,
        'name': driver.name,
        'team': driver.team,
        'carNumber': driver.car_number,
        'nationality': driver.nationality,
        'platform': driver.platform,
        'telemetrySettings': 'Public' if driver.is_telemetry_public else 'Restricted',
    }


def lap_to_api(lap: LapMetadata) -> Dict[str, Any]:
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
