# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import lib.overtake_analyzer as OvertakeAnalyzer
import lib.race_analyzer as RaceAnalyzer
from lib.f1_types import F1Utils, SessionType23, SessionType24

# Known session type strings derived from the authoritative enums, sorted longest-first
# so greedy prefix matching always picks the most specific match.
_KNOWN_SESSION_TYPES: List[str] = sorted(
    {str(s) for cls in (SessionType23, SessionType24) for s in cls if s.name != 'UNKNOWN'},
    key=lambda t: len(t.split()),
    reverse=True,
)

# Qualifying session types derived from the same enums.
_QUALIFYING_SESSION_TYPES: frozenset = frozenset(
    str(s) for cls in (SessionType23, SessionType24) for s in cls if s.isQualiTypeSession()
)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def find_json_files(session_dir: Path) -> List[Path]:
    """Recursively find all .json files under session_dir; paths relative to session_dir."""
    return [p.relative_to(session_dir) for p in session_dir.rglob('*.json')]


def to_slug(relative_path: Path) -> str:
    return relative_path.stem.lower().replace('_', '-')


def parse_filename(relative_path: Path) -> Dict[str, Any]:
    """Parse session metadata from filename. Pattern: [SessionType]_[Track]_[YYYY]_[MM]_[DD]_[HH]_[mm]_[ss].json"""
    stem = relative_path.stem
    parts = stem.split('_')
    date_parts = parts[-6:]
    date_str = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}T{date_parts[3]}:{date_parts[4]}:{date_parts[5]}"
    prefix = parts[:-6]

    session_type, track_start = _match_session_type(prefix)
    track = ' '.join(prefix[track_start:])

    return {
        'sessionType': session_type,
        'track': track,
        'date': date_str,
    }

def _match_session_type(prefix: List[str]) -> Tuple[str, int]:
    """Return (session_type_label, track_start_index) for the given prefix words."""
    for session_type in _KNOWN_SESSION_TYPES:
        words = session_type.split()
        n = len(words)
        if len(prefix) >= n and prefix[:n] == words:
            return session_type, n
    return (prefix[0] if prefix else ''), 1


def resolve_session_meta(relative_path: Path, session_info: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer in-JSON fields over filename-derived values."""
    filename_meta = parse_filename(relative_path)

    track_id = session_info.get('track-id')
    track = track_id.replace('_', ' ') if track_id else filename_meta['track']

    session_type = session_info.get('session-type') or filename_meta['sessionType']
    formula = session_info.get('formula')

    result = {
        'track': track,
        'sessionType': session_type,
        'date': filename_meta['date'],
    }
    if formula is not None:
        result['formula'] = formula
    return result


def _is_qualifying(session_type: str) -> bool:
    return session_type in _QUALIFYING_SESSION_TYPES


def build_session_list(session_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Scan session_dir for sessions and return (sessions, slug_map)."""
    if not session_dir.exists():
        return [], {}

    sessions = []
    for rel_path in find_json_files(session_dir):
        full_path = session_dir / rel_path
        slug = to_slug(rel_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session_info = data.get('session-info', {})
            meta = resolve_session_meta(rel_path, session_info)

            # Focus driver
            is_spectator = False
            focus_driver = None
            classification = data.get('classification-data', [])
            for driver in classification:
                if driver.get('is-player'):
                    focus_driver = driver
                    break
            if focus_driver is None:
                is_spectator = True
                # Pick driver with most valid laps
                best_count = -1
                for driver in classification:
                    lap_count = sum(
                        1 for lap in driver.get('lap-history-data', [])
                        if lap.get('lap-time-in-ms', 0) > 0
                    )
                    if lap_count > best_count:
                        best_count = lap_count
                        focus_driver = driver

            # validLapCount from focus driver
            valid_lap_count = 0
            if focus_driver:
                valid_lap_count = sum(
                    1 for lap in focus_driver.get('lap-history-data', [])
                    if lap.get('lap-time-in-ms', 0) > 0
                )

            session_entry: Dict[str, Any] = {
                'slug': slug,
                'sessionType': meta['sessionType'],
                'track': meta['track'],
                'date': meta['date'],
                'validLapCount': valid_lap_count,
                'isSpectator': is_spectator,
                'fileSize': full_path.stat().st_size,
                '_rel_path': str(rel_path),
            }
            if 'formula' in meta:
                session_entry['formula'] = meta['formula']

            network_game = session_info.get('network-game', 0)
            session_entry['aiDifficulty'] = 0 if network_game == 1 else session_info.get('ai-difficulty', 0)

            if _is_qualifying(meta['sessionType']) and focus_driver:
                lap_indicators = []
                best_lap_time_ms = None
                best_lap_time_str = None
                lap_history = focus_driver.get('lap-history-data', [])
                for lap in lap_history:
                    lap_ms = lap.get('lap-time-in-ms', 0)
                    valid_bits = lap.get('lap-validity-bit-flags', 0)
                    if lap_ms <= 0:
                        lap_indicators.append('invalid')
                    elif valid_bits & 0x01:
                        lap_indicators.append('valid')
                        if best_lap_time_ms is None or lap_ms < best_lap_time_ms:
                            best_lap_time_ms = lap_ms
                    else:
                        lap_indicators.append('invalid')

                # Mark best
                if best_lap_time_ms is not None:
                    for i, lap in enumerate(lap_history):
                        if lap.get('lap-time-in-ms') == best_lap_time_ms and lap_indicators[i] == 'valid':
                            lap_indicators[i] = 'best'
                            break
                    mins, remainder = divmod(best_lap_time_ms // 1000, 60)
                    ms = best_lap_time_ms % 1000
                    best_lap_time_str = f"{mins}:{remainder:02d}.{ms:03d}"

                session_entry['lapIndicators'] = lap_indicators
                if best_lap_time_ms is not None:
                    session_entry['bestLapTimeMs'] = best_lap_time_ms
                    session_entry['bestLapTime'] = best_lap_time_str

        except Exception:  # pylint: disable=broad-exception-caught
            filename_meta = parse_filename(rel_path)
            session_entry = {
                'slug': slug,
                'sessionType': filename_meta['sessionType'],
                'track': filename_meta['track'],
                'date': filename_meta['date'],
                'validLapCount': 0,
                'isSpectator': False,
                'fileSize': full_path.stat().st_size if full_path.exists() else 0,
                '_rel_path': str(rel_path),
                'aiDifficulty': 0,
            }

        if session_entry['validLapCount'] > 0:
            sessions.append(session_entry)

    # Deduplicate: group by formula|sessionType|track|validLapCount within 30-second window
    sessions = _deduplicate_sessions(sessions)

    # Sort newest-first
    sessions.sort(key=lambda s: s['date'], reverse=True)

    # Build slug_map from surviving sessions
    slug_map = {s['slug']: s.pop('_rel_path') for s in sessions}
    # Clean internal fields
    for s in sessions:
        s.pop('_rel_path', None)
        s.pop('fileSize', None)

    return sessions, slug_map


def _deduplicate_sessions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group by formula|sessionType|track|validLapCount; within 30-second window keep larger file."""
    def parse_date(date_str: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    # Sort by date for windowed grouping
    sessions_with_dt = [(s, parse_date(s['date'])) for s in sessions]
    sessions_with_dt.sort(key=lambda x: (x[1] or datetime.min.replace(tzinfo=timezone.utc)))

    survivors: List[Dict[str, Any]] = []

    for session, dt in sessions_with_dt:
        formula = session.get('formula', '')
        key = f"{formula}|{session['sessionType']}|{session['track']}|{session['validLapCount']}"
        matched = False
        for survivor in survivors:
            s_formula = survivor.get('formula', '')
            s_key = f"{s_formula}|{survivor['sessionType']}|{survivor['track']}|{survivor['validLapCount']}"
            if s_key != key:
                continue
            s_dt = parse_date(survivor['date'])
            if dt and s_dt and abs((dt - s_dt).total_seconds()) <= 30:
                # Keep larger file
                if session.get('fileSize', 0) > survivor.get('fileSize', 0):
                    # Replace survivor
                    idx = survivors.index(survivor)
                    duplicate_count = survivor.get('duplicateCount', 0) + 1
                    session['duplicateCount'] = duplicate_count
                    survivors[idx] = session
                else:
                    survivor['duplicateCount'] = survivor.get('duplicateCount', 0) + 1
                matched = True
                break
        if not matched:
            survivors.append(session)

    return survivors


def load_session_json(
    session_dir: Path,
    slug_map: Dict[str, str],
    slug: str
) -> Optional[Dict[str, Any]]:
    """Resolve slug to file, validate path, load JSON, apply recompute. Returns None on any error."""
    relative_str = slug_map.get(slug)
    if relative_str is None:
        return None

    root = session_dir.resolve()
    full = (root / relative_str).resolve()
    if not full.is_relative_to(root):
        return None

    try:
        with open(full, 'r', encoding='utf-8') as f:
            data = json.load(f)
        check_recompute_json(data)
        return data
    except Exception:  # pylint: disable=broad-exception-caught
        return None


# -------------------------------------- RECOMPUTE HELPERS -------------------------------------------------------------

def check_recompute_json(json_data: Dict[str, Any]) -> bool:
    """Check and fill in missing derived fields in race JSON data."""
    updated = False
    updated |= _fill_missing_tyre_wear(json_data)
    updated |= _ensure_records_container(json_data)
    updated |= _ensure_fastest_records(json_data)
    updated |= _ensure_tyre_stats(json_data)
    updated |= _ensure_overtake_records(json_data)
    return updated


def _is_valid_json(data: Any) -> bool:
    """Return True if data is already a dict or a valid JSON string."""
    if isinstance(data, dict):
        return True
    try:
        json.loads(data)
        return True
    except json.JSONDecodeError:
        return False


def _get_tyre_wear_history(driver_data: Dict[str, Any], start_lap: int, end_lap: int) -> List[Dict[str, Any]]:
    """Extract per-corner tyre wear for laps in [start_lap, end_lap] from a driver's per-lap-info."""
    tyre_wear_history = []
    if 'per-lap-info' in driver_data:
        for lap_backup in driver_data['per-lap-info']:
            lap_number = lap_backup['lap-number']
            if not (start_lap <= lap_number <= end_lap):
                continue
            if 'car-damage-data' in lap_backup:
                wear = lap_backup['car-damage-data']['tyres-wear']
                tyre_wear_history.append({
                    'lap-number': lap_number,
                    'front-left-wear': wear[F1Utils.INDEX_FRONT_LEFT],
                    'front-right-wear': wear[F1Utils.INDEX_FRONT_RIGHT],
                    'rear-left-wear': wear[F1Utils.INDEX_REAR_LEFT],
                    'rear-right-wear': wear[F1Utils.INDEX_REAR_RIGHT],
                })
    return tyre_wear_history


def _fill_missing_tyre_wear(json_data: Dict[str, Any]) -> bool:
    """Backfill tyre-wear-history on any stint that is missing it. Returns True if any stint was updated."""
    updated = False
    if 'classification-data' in json_data:
        for driver_data in json_data['classification-data']:
            if not (tyre_set_history := driver_data.get('tyre-set-history')):
                continue
            for stint in tyre_set_history:
                if 'tyre-wear-history' not in stint:
                    stint['tyre-wear-history'] = _get_tyre_wear_history(
                        driver_data, stint['start-lap'], stint['end-lap']
                    )
                    updated = True
    return updated


def _ensure_fastest_records(json_data: Dict[str, Any]) -> bool:
    """Ensure records['fastest'] exists and contains all expected keys; recomputes if missing or stale."""
    if 'fastest' not in json_data['records']:
        json_data['records']['fastest'] = RaceAnalyzer.getFastestTimesJson(json_data)
        return True

    expected_keys = ['driver-index', 'driver-name', 'team-id', 'lap-number', 'time', 'time-str']
    for record in json_data['records']['fastest'].values():
        if any(key not in record for key in expected_keys):
            json_data['records']['fastest'] = RaceAnalyzer.getFastestTimesJson(json_data)
            return True
    return False


def _ensure_tyre_stats(json_data: Dict[str, Any]) -> bool:
    """Ensure records['tyre-stats'] exists and contains all expected keys; recomputes if missing or stale."""
    if 'tyre-stats' not in json_data['records']:
        json_data['records']['tyre-stats'] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
        return True

    required_keys = ['longest-tyre-stint', 'lowest-tyre-wear-per-lap', 'highest-tyre-wear']
    for compound_stats in json_data['records']['tyre-stats'].values():
        if any(key not in compound_stats for key in required_keys):
            json_data['records']['tyre-stats'] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
            return True
    return False


def _ensure_overtake_records(json_data: Dict[str, Any]) -> bool:
    """Ensure overtakes summary keys exist; re-runs OvertakeAnalyzer if the enriched fields are absent."""
    if 'overtakes' not in json_data:
        json_data['overtakes'] = {'records': []}
        return True

    required_keys = ['number-of-overtakes', 'most-heated-rivalries']
    missing_keys = any(key not in json_data['overtakes'] for key in required_keys)
    if not missing_keys:
        return False

    records = json_data['overtakes'].get('records', [])
    if not records:
        return True

    mode = (
        OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS_JSON
        if _is_valid_json(records[0])
        else OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV
    )

    enriched = OvertakeAnalyzer.OvertakeAnalyzer(
        input_mode=mode,
        input_data=records
    ).toJSON()

    json_data['overtakes'] = {**json_data['overtakes'], **enriched}
    return True


def _ensure_records_container(json_data: Dict[str, Any]) -> bool:
    """Create the top-level 'records' dict with fastest and tyre-stats if it doesn't exist yet."""
    if 'records' not in json_data:
        json_data['records'] = {
            'fastest': RaceAnalyzer.getFastestTimesJson(json_data),
            'tyre-stats': RaceAnalyzer.getTyreStintRecordsDict(json_data),
        }
        return True
    return False
