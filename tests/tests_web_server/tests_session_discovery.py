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
# pylint: skip-file

"""Session discovery: filename parsing and session-list building.

Regression cover for the crash where a single `.json` whose name didn't match
`[Type]_[Track]_[YYYY]_[MM]_[DD]_[HH]_[mm]_[ss].json` raised IndexError out of
`parse_filename`, aborting the whole cache build (and skipping the cache write,
so every startup re-parsed the entire directory and failed again).
"""

import json
import logging
from pathlib import Path

import pytest

from apps.web.session_discovery import (CACHE_FILE, _normalize_saved_at,
                                        build_session_list, load_session_json,
                                        parse_filename, to_slug)
from lib.logger import PngLogger
from lib.pngt import (CompletedLap, DriverExportData, DriverRecord,
                      LapMetadata, SensorConfig, SensorType, SessionDataEntry,
                      SessionMetadata, TrackInfo, write_session,
                      write_session_data_only)

# ----------------------------------------------------------------------------------------------------------------------

logging.setLoggerClass(PngLogger)

_SAVED_AT = '2026-08-31 01:58:46 IST'
_EXPECTED_DATE = '2026-08-31T01:58:46'
_GOOD_NAME = 'Race_Sakhir_2026_08_31_01_58_46.json'


def _logger() -> PngLogger:
    return logging.getLogger("test_session_discovery")


def _save(saved_at: str = _SAVED_AT) -> dict:
    """A minimal but realistic P&G save payload."""
    return {
        'session-info': {
            'track-id': 'Sakhir',
            'session-type': 'Race',
            'formula': 'F1 Modern',
        },
        'classification-data': [{
            'is-player': True,
            'session-history': {
                'lap-history-data': [{'lap-time-in-ms': 95000, 'lap-valid-bit-flags': 15}],
            },
        }],
        'debug': {'timestamp': saved_at},
    }


def _lap_session():
    return SessionMetadata(
        session_uid=1, session_name="Test", session_type="race", app_version="0.0.1-test", game_year=2026,
        formula="F1", game_version="1.00", timestamp="2024-06-01T14:32:00Z", track=TrackInfo(id=999, name="Fake"))


def _lap_sensors():
    return [SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)]


def _lap_drivers():
    return [DriverRecord(driver_index=1, name="Driver A", team="Team A", car_number=1,
                         nationality="GB", platform="Steam")]


def _lap_driver_data():
    lap = CompletedLap(
        metadata=LapMetadata(lap_number=1, lap_time_ms=90000, valid=True, tyre_compound="Soft",
                             tyre_laps=1, pit_in_lap=False, pit_out_lap=False, ers_harvest_limit_j=None),
        telemetry={"lap_distance": [0.0, 100.0], "speed": [100.0, 110.0]})
    return {1: DriverExportData(driver_index=1, completed_laps=[lap])}


def _write(directory: Path, name: str, payload) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')
    return path


async def _build(session_dir: Path) -> list:
    sessions = []
    async for batch, _slug_map in build_session_list(session_dir, _logger(), '0.0.0-test'):
        sessions = batch
    return sessions


# -------------------------------------- parse_filename ----------------------------------------------------------------

def test_parse_filename_reads_a_well_formed_name():
    meta = parse_filename(Path(_GOOD_NAME))
    assert meta == {'sessionType': 'Race', 'track': 'Sakhir', 'date': _EXPECTED_DATE}


def test_parse_filename_handles_multi_word_session_types():
    meta = parse_filename(Path('Short_Qualifying_Zandvoort_2026_02_07_11_33_48.json'))
    assert meta['sessionType'] == 'Short Qualifying'
    assert meta['track'] == 'Zandvoort'


@pytest.mark.parametrize('name', [
    'awesome_race.json',          # user-renamed save - the reported crash
    'notes.json',                 # foreign single-word file
    'sessions.json',              # the save-viewer's own demo index
    'a_b_c_d_e.json',             # five segments: one short of the slice
    'Race_Spa_2026_08_31_01_58.json',      # truncated date
    'one_two_three_four_five_six.json',    # six segments, but not digits
])
def test_parse_filename_never_raises_on_a_non_conforming_name(name):
    """Filenames are user-editable, so this must degrade rather than raise."""
    meta = parse_filename(Path(name))
    assert meta['date'] == ''
    assert meta['track'] == Path(name).stem
    assert meta['sessionType'] == ''


# -------------------------------------- _normalize_saved_at -----------------------------------------------------------

@pytest.mark.parametrize('saved_at,expected', [
    ('2026-08-31 01:58:46 IST', '2026-08-31T01:58:46'),
    # Windows hands back multi-word zone names from %Z - only the first two fields count
    ('2026-01-26 22:14:52 GMT Standard Time', '2026-01-26T22:14:52'),
    ('2026-01-26 22:14:52 ', '2026-01-26T22:14:52'),
    ('2026-01-26 22:14:52', '2026-01-26T22:14:52'),
    ('garbage', ''),
    ('', ''),
    (None, ''),
])
def test_normalize_saved_at(saved_at, expected):
    assert _normalize_saved_at(saved_at) == expected


# -------------------------------------- build_session_list ------------------------------------------------------------

async def test_renaming_a_save_preserves_all_of_its_metadata(tmp_path):
    """The filename is cosmetic: metadata comes from inside the file."""
    _write(tmp_path, _GOOD_NAME, _save())
    _write(tmp_path, 'awesome_race.json', _save())

    by_slug = {s['slug']: s for s in await _build(tmp_path)}
    original = by_slug[to_slug(Path(_GOOD_NAME))]
    renamed = by_slug['awesome-race']

    for field in ('sessionType', 'track', 'date', 'formula', 'validLapCount'):
        assert renamed[field] == original[field], f'{field} did not survive the rename'
    assert renamed['date'] == _EXPECTED_DATE


async def test_one_unparseable_file_does_not_take_down_the_others(tmp_path):
    """The reported bug: a single bad name aborted the entire build."""
    _write(tmp_path, _GOOD_NAME, _save())
    _write(tmp_path, 'notes.json', {'hello': 'world'})
    _write(tmp_path, 'sessions.json', [1, 2, 3])   # top-level array: not a dict

    sessions = await _build(tmp_path)

    assert len(sessions) == 3
    good = next(s for s in sessions if s['slug'] == to_slug(Path(_GOOD_NAME)))
    assert good['date'] == _EXPECTED_DATE
    assert good['track'] == 'Sakhir'


async def test_cache_is_written_even_when_a_file_is_unparseable(tmp_path):
    """Aborting before the cache write made every startup re-parse the whole directory."""
    _write(tmp_path, _GOOD_NAME, _save())
    _write(tmp_path, 'notes.json', {'hello': 'world'})

    await _build(tmp_path)

    assert (tmp_path / CACHE_FILE).exists()


async def test_entries_always_carry_a_sortable_date(tmp_path):
    """A blank date would silently sink the session to the bottom of the list."""
    _write(tmp_path, 'notes.json', {'hello': 'world'})

    entry = (await _build(tmp_path))[0]

    assert entry['date']            # falls back to the file mtime
    assert entry['date'] != ''


async def test_in_file_timestamp_wins_over_a_contradictory_filename(tmp_path):
    """`debug.timestamp` is authoritative; the filename's date is only a fallback."""
    _write(tmp_path, 'Race_Sakhir_1999_01_01_00_00_00.json', _save())

    entry = (await _build(tmp_path))[0]

    assert entry['date'] == _EXPECTED_DATE


async def test_filename_date_is_used_when_the_save_has_no_timestamp(tmp_path):
    """Older saves predate the debug block - they must still order correctly."""
    payload = _save()
    del payload['debug']
    _write(tmp_path, _GOOD_NAME, payload)

    entry = (await _build(tmp_path))[0]

    assert entry['date'] == _EXPECTED_DATE


# -------------------------------------- .pngt containers --------------------------------------------------------------

def _container(directory: Path, name: str, payload=None, *, lap_telemetry: bool = False) -> Path:
    """A .pngt holding `payload` as its session_data section, plus a lap recording if asked."""
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = None if payload is None else SessionDataEntry(
        Path(name).with_suffix('.json').name, json.dumps(payload).encode('utf-8'))
    if lap_telemetry:
        write_session(path, _lap_session(), _lap_sensors(), _lap_drivers(), _lap_driver_data(), session_data=entry)
    else:
        write_session_data_only(path, entry)
    return path


async def test_session_data_only_container_is_listed(tmp_path):
    _container(tmp_path, _GOOD_NAME.replace('.json', '.pngt'), _save())

    sessions = await _build(tmp_path)

    assert [s['track'] for s in sessions] == ['Sakhir']
    assert sessions[0]['date'] == _EXPECTED_DATE
    assert sessions[0]['validLapCount'] == 1


async def test_container_with_lap_telemetry_is_listed_by_its_session_data(tmp_path):
    _container(tmp_path, _GOOD_NAME.replace('.json', '.pngt'), _save(), lap_telemetry=True)

    sessions = await _build(tmp_path)

    assert [s['track'] for s in sessions] == ['Sakhir']


async def test_container_without_session_data_is_not_listed(tmp_path):
    """A lap recording on its own is the lap analyzer's file, not a save-viewer session."""
    _container(tmp_path, 'Race_Spa_2026_08_31_01_58_46.pngt', lap_telemetry=True)
    _write(tmp_path, _GOOD_NAME, _save())

    sessions = await _build(tmp_path)

    assert [s['track'] for s in sessions] == ['Sakhir']


async def test_loose_json_and_container_are_listed_together(tmp_path):
    _write(tmp_path, _GOOD_NAME, _save())
    _container(tmp_path, 'Race_Spa_2026_09_01_01_58_46.pngt', _save(), lap_telemetry=True)

    assert len(await _build(tmp_path)) == 2


async def test_container_session_data_loads_by_slug(tmp_path, monkeypatch):
    # The minimal payload is not a full save, so skip the derived-field recompute
    monkeypatch.setattr('apps.web.session_discovery.check_recompute_json', lambda _data: False)
    _container(tmp_path, _GOOD_NAME.replace('.json', '.pngt'), _save())
    slug_map = {}
    async for _sessions, slug_map in build_session_list(tmp_path, _logger(), '0.0.0-test'):
        pass

    data = await load_session_json(tmp_path, slug_map, to_slug(Path(_GOOD_NAME)))

    assert data['session-info']['track-id'] == 'Sakhir'


async def test_load_session_json_none_for_container_without_session_data(tmp_path):
    path = _container(tmp_path, 'Race_Spa_2026_08_31_01_58_46.pngt', lap_telemetry=True)

    assert await load_session_json(tmp_path, {'x': path.name}, 'x') is None


async def test_corrupt_container_does_not_take_down_the_others(tmp_path):
    (tmp_path / 'Race_Spa_2026_09_01_01_58_46.pngt').write_bytes(b'not a zip')
    _write(tmp_path, _GOOD_NAME, _save())

    sessions = await _build(tmp_path)

    assert 'Sakhir' in [s['track'] for s in sessions]
