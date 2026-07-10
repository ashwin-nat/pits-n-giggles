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

import asyncio
import time
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import aiofiles
import orjson
from async_lru import alru_cache

import lib.overtake_analyzer as OvertakeAnalyzer
import lib.race_analyzer as RaceAnalyzer
from lib.f1_types import (F1Utils, PacketSessionData, SessionType23,
                          SessionType24)
from lib.logger import PngLogger

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

CACHE_FILE = '.png_session_cache.json'
_JSON_CACHE_SIZE = 25

# Known session type strings derived from the authoritative enums, sorted longest-first
# so greedy prefix matching always picks the most specific match.
_KNOWN_SESSION_TYPES: List[str] = sorted(
    {str(s) for cls in (SessionType23, SessionType24) for s in cls if s.name != 'UNKNOWN'},
    key=lambda t: len(t.split()),
    reverse=True,
)

_QUALIFYING_SESSION_TYPES: frozenset = frozenset(
    str(s) for cls in (SessionType23, SessionType24) for s in cls if s.isQualiTypeSession()
)
_RACE_SESSION_TYPES: frozenset = frozenset(
    str(s) for cls in (SessionType23, SessionType24) for s in cls if s.isRaceTypeSession()
)
_F1_FORMULA_STRINGS: frozenset = frozenset(
    str(f) for f in PacketSessionData.FormulaType if f.is_f1()
)
_PARSE_CONCURRENCY = 50

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def find_json_files(session_dir: Path) -> List[Path]:
    """Recursively find all .json files under session_dir; paths relative to session_dir."""
    return [
        p.relative_to(session_dir)
        for p in session_dir.rglob('*.json')
        if not p.name.startswith('.')
    ]


def _load_cache(cache_path: Path) -> Dict[str, Any]:
    try:
        with open(cache_path, 'rb') as f:
            return orjson.loads(f.read())
    except (FileNotFoundError, orjson.JSONDecodeError):
        return {}


def _save_cache(cache_path: Path, cache: Dict[str, Any]) -> None:
    with open(cache_path, 'wb') as f:
        f.write(orjson.dumps(cache))


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



def _is_qualifying_session(session_type: str) -> bool:
    return session_type in _QUALIFYING_SESSION_TYPES


def _is_race_session(session_type: str) -> bool:
    return session_type in _RACE_SESSION_TYPES


def formula_group_key(formula: str) -> str:
    """Map a formula string to its comparison group key.
    All F1 variants (F1 Modern, F1 Classic, etc.) collapse to 'f1'."""
    return 'f1' if formula in _F1_FORMULA_STRINGS else formula


def _get_clean_race_laps(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Port of getCleanRaceLaps from stats.ts: filters out lap 1, SC laps, pit laps, and outliers."""
    sh = player.get('session-history', {})
    laps = sh.get('lap-history-data', [])
    per_lap_info = player.get('per-lap-info', [])
    tyre_set_history = player.get('tyre-set-history', [])

    pit_laps: set = set()
    for stint in tyre_set_history[:-1]:
        end_lap = stint.get('end-lap', 0)
        pit_laps.add(end_lap)
        pit_laps.add(end_lap + 1)

    sc_by_lap = {p['lap-number']: p.get('max-safety-car-status', 'NO_SAFETY_CAR') for p in per_lap_info}

    clean = []
    for i, lap in enumerate(laps[1:], start=2):  # skip lap 1; lap numbers are 1-indexed
        if lap.get('lap-valid-bit-flags') != 15 or lap.get('lap-time-in-ms', 0) <= 0:
            continue
        if sc_by_lap.get(i, 'NO_SAFETY_CAR') != 'NO_SAFETY_CAR':
            continue
        if i in pit_laps:
            continue
        clean.append(lap)

    if len(clean) < 3:
        return clean

    times = sorted(l['lap-time-in-ms'] for l in clean)
    median = times[len(times) // 2]
    return [l for l in clean if l['lap-time-in-ms'] <= median * 1.2]


def _parse_session_metadata(path: Path, logger: PngLogger) -> Dict[str, Any]:
    """Load a session JSON and extract session-info plus player lap stats."""
    logger.debug("_parse_session_metadata: reading %s (%.1f MB)", path.name, path.stat().st_size / 1_048_576)
    with open(path, 'rb') as fh:
        data = orjson.loads(fh.read())

    session_info = data.get('session-info', {})
    classification = data.get('classification-data', [])

    player = next((d for d in classification if d.get('is-player')), None)
    is_spectator = player is None
    if is_spectator:
        player = max(
            classification,
            key=lambda d: sum(
                1 for l in d.get('session-history', {}).get('lap-history-data', [])
                if l.get('lap-time-in-ms', 0) > 0
            ),
            default=None,
        )

    result: Dict[str, Any] = {'session_info': session_info, 'is_spectator': is_spectator}

    if player:
        sh = player.get('session-history', {})
        laps = sh.get('lap-history-data', [])
        driven = [l for l in laps if l.get('lap-time-in-ms', 0) > 0]
        result['valid_lap_count'] = len(driven)

        session_type = session_info.get('session-type', '')
        if _is_qualifying_session(session_type):
            best_lap_num = sh.get('best-lap-time-lap-num', -1)
            result['lap_indicators'] = [
                'best' if (i + 1) == best_lap_num
                else ('valid' if l.get('lap-valid-bit-flags') == 15 else 'invalid')
                for i, l in enumerate(driven)
            ]
            if 0 < best_lap_num <= len(laps):
                best = laps[best_lap_num - 1]
                if best.get('lap-time-in-ms'):
                    result['best_lap_time_ms'] = best['lap-time-in-ms']
                    result['best_lap_time_str'] = best.get('lap-time-str')

            valid = [l for l in laps if l.get('lap-valid-bit-flags') == 15 and l.get('lap-time-in-ms', 0) > 0]
            for idx, sector_key in enumerate(('sector-1-time-in-ms', 'sector-2-time-in-ms', 'sector-3-time-in-ms'), 1):
                times = [l[sector_key] for l in valid if l.get(sector_key, 0) > 0]
                if times:
                    result[f'best_s{idx}_ms'] = min(times)

        elif _is_race_session(session_type):
            valid = [l for l in laps if l.get('lap-valid-bit-flags') == 15 and l.get('lap-time-in-ms', 0) > 0]
            if valid:
                result['best_race_lap_ms'] = min(l['lap-time-in-ms'] for l in valid)
            clean = _get_clean_race_laps(player)
            if clean:
                result['best_race_pace_ms'] = sum(l['lap-time-in-ms'] for l in clean) / len(clean)
    else:
        result['valid_lap_count'] = 0

    return result

async def _parse_one(
    file_idx: int,
    total: int,
    rel_path: Path,
    full_path: Path,
    logger: PngLogger,
    cache: Dict[str, Any],
) -> Tuple[Path, Any]:
    """Return (rel_path, session_info | Exception), using the mtime cache to skip unchanged files."""
    cache_key = str(rel_path)
    try:
        mtime = full_path.stat().st_mtime
    except OSError:
        mtime = 0.0

    cached = cache.get(cache_key)
    if cached and cached.get('mtime') == mtime and 'data' in cached:
        return rel_path, cached['data']

    try:
        start = time.perf_counter()
        parsed = await asyncio.to_thread(_parse_session_metadata, full_path, logger)
        logger.debug("[%d/%d] done in %.2fs — %s", file_idx, total, time.perf_counter() - start, rel_path)
        cache[cache_key] = {'mtime': mtime, 'data': parsed}
        return rel_path, parsed
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.silent("[%d/%d] failed — %s: %s", file_idx, total, rel_path, exc)
        return rel_path, exc


def _sort_files_newest_first(json_files: List[Path]) -> List[Path]:
    """Sort file paths newest-first using the date embedded in each filename (no disk I/O)."""
    def _date_key(p: Path) -> str:
        try:
            return parse_filename(p)['date']
        except Exception:  # pylint: disable=broad-exception-caught
            return ''
    return sorted(json_files, key=_date_key, reverse=True)


def _make_session_entry(
    rel_path: Path,
    full_path: Path,
    outcome: Any,
) -> Dict[str, Any]:
    """Build a session entry dict from a parse outcome (session_info dict or Exception)."""
    slug = to_slug(rel_path)
    if isinstance(outcome, Exception):
        filename_meta = parse_filename(rel_path)
        return {
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

    session_info = outcome['session_info']
    meta = resolve_session_meta(rel_path, session_info)
    network_game = session_info.get('network-game', 0)
    entry: Dict[str, Any] = {
        'slug': slug,
        'sessionType': meta['sessionType'],
        'track': meta['track'],
        'date': meta['date'],
        'validLapCount': outcome.get('valid_lap_count', 0),
        'isSpectator': outcome.get('is_spectator', False),
        'fileSize': full_path.stat().st_size,
        '_rel_path': str(rel_path),
        'aiDifficulty': 0 if network_game == 1 else session_info.get('ai-difficulty', 0),
    }
    if 'formula' in meta:
        entry['formula'] = meta['formula']
    if lap_indicators := outcome.get('lap_indicators'):
        entry['lapIndicators'] = lap_indicators
    if best_ms := outcome.get('best_lap_time_ms'):
        entry['bestLapTimeMs'] = best_ms
        if best_str := outcome.get('best_lap_time_str'):
            entry['bestLapTime'] = best_str
    for src, dst in (
        ('best_s1_ms', 'bestS1Ms'), ('best_s2_ms', 'bestS2Ms'), ('best_s3_ms', 'bestS3Ms'),
        ('best_race_lap_ms', 'bestRaceLapMs'), ('best_race_pace_ms', 'bestRacePaceMs'),
    ):
        if val := outcome.get(src):
            entry[dst] = val
    return entry


def _snapshot(all_raw: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Sort + build slug_map from the running raw list. Non-destructive."""
    candidates = [dict(e) for e in all_raw]
    candidates.sort(key=lambda s: s['date'], reverse=True)
    slug_map = {s['slug']: s.pop('_rel_path') for s in candidates}
    for s in candidates:
        s.pop('fileSize', None)
    return candidates, slug_map


async def build_session_list(
    session_dir: Path,
    logger: PngLogger,
) -> AsyncIterator[Tuple[List[Dict[str, Any]], Dict[str, str]]]:
    """Async generator: yields (sessions, slug_map) after each batch of _PARSE_CONCURRENCY files.

    Files are processed newest-first so the most recent sessions are available
    after the very first yield. Metadata is cached on disk keyed by file mtime,
    so only new or modified files are parsed on subsequent runs.
    """
    if not session_dir.exists():
        return

    json_files = find_json_files(session_dir)
    logger.debug("build_session_list: found %d JSON files in %s", len(json_files), session_dir)

    json_files = _sort_files_newest_first(json_files)
    total = len(json_files)

    cache_path = session_dir / CACHE_FILE
    cache_file_existed = cache_path.exists()
    cache: Dict[str, Any] = await asyncio.to_thread(_load_cache, cache_path)
    cache_hits = sum(1 for r in json_files if str(r) in cache)

    if not cache_file_existed:
        logger.info("Session cache: no cache file found, parsing all %d files from scratch", total)
    elif not cache:
        logger.warning("Session cache: cache file invalid or empty, parsing all %d files from scratch", total)
    elif cache_hits < total:
        logger.info("Session cache: %d new/modified files to parse (%d/%d already cached)",
                    total - cache_hits, cache_hits, total)
    else:
        logger.debug("Session cache: all %d files already cached", total)

    all_raw: List[Dict[str, Any]] = []

    for batch_start in range(0, total, _PARSE_CONCURRENCY):
        batch = json_files[batch_start:batch_start + _PARSE_CONCURRENCY]
        results = await asyncio.gather(
            *[
                _parse_one(batch_start + i + 1, total, rel, session_dir / rel, logger, cache)
                for i, rel in enumerate(batch)
            ]
        )

        for rel_path, outcome in results:
            all_raw.append(_make_session_entry(rel_path, session_dir / rel_path, outcome))

        sessions, slug_map = _snapshot(all_raw)
        batch_end = min(batch_start + _PARSE_CONCURRENCY, total)
        logger.debug(
            "build_session_list: files %d-%d/%d done — %d sessions so far",
            batch_start + 1, batch_end, total, len(sessions),
        )
        yield sessions, slug_map

    # Prune deleted files and persist the updated cache
    live_keys = {str(r) for r in json_files}
    pruned_cache = {k: v for k, v in cache.items() if k in live_keys}
    await asyncio.to_thread(_save_cache, cache_path, pruned_cache)
    # logger.info("build_session_list: cache saved (%d entries)", len(pruned_cache))



@alru_cache(maxsize=_JSON_CACHE_SIZE)
async def _cached_load(full_path_str: str) -> Dict[str, Any]:
    """Read, parse, and recompute a session JSON file. Results are LRU-cached by path."""
    async with aiofiles.open(full_path_str, 'rb') as f:
        data = orjson.loads(await f.read())
    check_recompute_json(data)
    return data


async def load_session_json(
    session_dir: Path,
    slug_map: Dict[str, str],
    slug: str
) -> Optional[Dict[str, Any]]:
    """Resolve slug to file, validate path, load and cache JSON. Returns None on any error."""
    relative_str = slug_map.get(slug)
    if relative_str is None:
        return None

    root = session_dir.resolve()
    full = (root / relative_str).resolve()
    if not full.is_relative_to(root):
        return None

    try:
        return await _cached_load(str(full))
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
        orjson.loads(data)
        return True
    except orjson.JSONDecodeError:
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
