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

"""Discovers .pngt telemetry recordings in the session directory and caches their
parsed metadata (session/drivers/laps/sensor manifest) on top of lib/file_discovery.py's
generic scan/cache engine. No route handlers here -- this is the data layer the
lap-analyzer API routes (a later commit) read from.

Deliberately excluded from the cache: per-lap telemetry (the NPZ sensor arrays). Only
one lap is ever being viewed at a time, so caching it here would mean holding
potentially many megabytes per lap in memory for no benefit -- it's read fresh from
the archive on every GET /telemetry/... call instead.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from lib.logger import PngLogger
from lib.pngt import (ParsedDriver, ParsedLap, ParsedSessionMetadata,
                      PngtError, SensorConfig, SensorType, SessionBest,
                      TrackInfo, read_driver_laps, read_session)

from lib.file_discovery import DiscoveryConfig, discover_all, find_files

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

CACHE_FILE = '.png_pngt_cache.json.gz'
_GLOB = '*.pngt'

_SLUG_INVALID = re.compile(r'[^a-z0-9]+')

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class PngtSessionEntry:
    """Everything the sessions/drivers/laps read endpoints need for one .pngt file,
    parsed once via lib.pngt.reader and cached by file mtime."""
    slug: str
    rel_path: str
    session: ParsedSessionMetadata
    drivers: List[ParsedDriver]
    sensors: List[SensorConfig]
    laps_by_driver: Dict[int, List[ParsedLap]]


@dataclass(frozen=True)
class _ParsedPngtFile:
    """Raw parse output, before slug assignment -- see `_make_entry` for why slug
    assignment is a separate step that never runs inside the threaded parse."""
    session: ParsedSessionMetadata
    drivers: List[ParsedDriver]
    sensors: List[SensorConfig]
    laps_by_driver: Dict[int, List[ParsedLap]]

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def find_pngt_files(session_dir: Path) -> List[Path]:
    """Recursively find all .pngt files under session_dir; paths relative to session_dir."""
    return find_files(session_dir, _GLOB)


def slugify(name: str) -> str:
    """Lowercase, hyphenate. Never returns an empty string -- an all-punctuation or
    empty name falls back to 'session' so a slug always exists."""
    slug = _SLUG_INVALID.sub('-', name.strip().lower()).strip('-')
    return slug or 'session'


def _unique_slug(base: str, taken: set) -> str:
    """First-discovery-only collision guard: if `base` is already used by a
    different file, append -2, -3, ... until free."""
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"

# ---- ParsedSessionMetadata / ParsedDriver / ParsedLap / SensorConfig <-> plain dict ----
# Explicit field-by-field, mirroring lib/pngt/reader.py's own style, rather than
# dataclasses.asdict()+reconstruct -- keeps this cache format decoupled from the
# dataclass definitions' field order/shape and makes exactly what's persisted visible
# at a glance.

def _session_to_dict(session: ParsedSessionMetadata) -> Dict[str, Any]:
    return {
        'session_uid': session.session_uid,
        'session_name': session.session_name,
        'session_type': session.session_type,
        'app_version': session.app_version,
        'game_year': session.game_year,
        'formula': session.formula,
        'game_version': session.game_version,
        'timestamp': session.timestamp,
        'track': {'id': session.track.id, 'name': session.track.name},
        'laps_count': session.laps_count,
        'session_best': None if session.session_best is None else {
            'driver_index': session.session_best.driver_index,
            'lap_number': session.session_best.lap_number,
            'lap_time_ms': session.session_best.lap_time_ms,
        },
    }


def _dict_to_session(raw: Dict[str, Any]) -> ParsedSessionMetadata:
    session_best_raw = raw.get('session_best')
    return ParsedSessionMetadata(
        session_uid=raw['session_uid'],
        session_name=raw['session_name'],
        session_type=raw['session_type'],
        app_version=raw['app_version'],
        game_year=raw['game_year'],
        formula=raw['formula'],
        game_version=raw['game_version'],
        timestamp=raw['timestamp'],
        track=TrackInfo(id=raw['track']['id'], name=raw['track']['name']),
        laps_count=raw['laps_count'],
        session_best=None if session_best_raw is None else SessionBest(
            driver_index=session_best_raw['driver_index'],
            lap_number=session_best_raw['lap_number'],
            lap_time_ms=session_best_raw['lap_time_ms'],
        ),
    )


def _driver_to_dict(driver: ParsedDriver) -> Dict[str, Any]:
    return {
        'driver_index': driver.driver_index,
        'name': driver.name,
        'team': driver.team,
        'car_number': driver.car_number,
        'nationality': driver.nationality,
        'platform': driver.platform,
        'is_telemetry_public': driver.is_telemetry_public,
    }


def _dict_to_driver(raw: Dict[str, Any]) -> ParsedDriver:
    return ParsedDriver(
        driver_index=raw['driver_index'],
        name=raw['name'],
        team=raw['team'],
        car_number=raw['car_number'],
        nationality=raw.get('nationality'),
        platform=raw.get('platform'),
        is_telemetry_public=raw['is_telemetry_public'],
    )


def _lap_to_dict(lap: ParsedLap) -> Dict[str, Any]:
    return {
        'lap_number': lap.lap_number,
        'lap_time_ms': lap.lap_time_ms,
        'valid': lap.valid,
        'tyre_compound': lap.tyre_compound,
        'tyre_laps': lap.tyre_laps,
        'pit_in_lap': lap.pit_in_lap,
        'pit_out_lap': lap.pit_out_lap,
        'num_points': lap.num_points,
        'is_good': lap.is_good,
    }


def _dict_to_lap(raw: Dict[str, Any]) -> ParsedLap:
    return ParsedLap(
        lap_number=raw['lap_number'],
        lap_time_ms=raw.get('lap_time_ms'),
        valid=raw['valid'],
        tyre_compound=raw['tyre_compound'],
        tyre_laps=raw['tyre_laps'],
        pit_in_lap=raw['pit_in_lap'],
        pit_out_lap=raw['pit_out_lap'],
        num_points=raw.get('num_points', 0),
        is_good=raw['is_good'],
    )


def _sensor_to_dict(sensor: SensorConfig) -> Dict[str, Any]:
    d = {'key': sensor.key, 'label': sensor.label, 'unit': sensor.unit, 'type': sensor.type.value}
    if sensor.range is not None:
        d['range'] = list(sensor.range)
    return d


def _dict_to_sensor(raw: Dict[str, Any]) -> SensorConfig:
    return SensorConfig(
        key=raw['key'],
        label=raw['label'],
        unit=raw['unit'],
        type=SensorType(raw['type']),
        range=tuple(raw['range']) if 'range' in raw else None,
    )

# ---- DiscoveryConfig plumbing ----

def _parse(full_path: Path) -> _ParsedPngtFile:
    """Reads one .pngt file's session/drivers/sensors/laps in full via lib.pngt.reader.
    Runs inside asyncio.to_thread via the generic engine -- must not touch shared
    state, which is exactly why slug assignment isn't done here (see `_make_entry`).
    """
    parsed = read_session(full_path)
    laps_by_driver = {
        driver.driver_index: read_driver_laps(full_path, driver.driver_index)
        for driver in parsed.drivers
    }
    return _ParsedPngtFile(
        session=parsed.session,
        drivers=parsed.drivers,
        sensors=parsed.sensors,
        laps_by_driver=laps_by_driver,
    )


def _entry_to_cache_dict(entry: PngtSessionEntry) -> Dict[str, Any]:
    return {
        'slug': entry.slug,
        'session': _session_to_dict(entry.session),
        'drivers': [_driver_to_dict(d) for d in entry.drivers],
        'sensors': [_sensor_to_dict(s) for s in entry.sensors],
        'laps_by_driver': {
            str(idx): [_lap_to_dict(lap) for lap in laps]
            for idx, laps in entry.laps_by_driver.items()
        },
    }


def _cache_dict_to_entry(rel_path: str, raw: Dict[str, Any]) -> PngtSessionEntry:
    return PngtSessionEntry(
        slug=raw['slug'],
        rel_path=rel_path,
        session=_dict_to_session(raw['session']),
        drivers=[_dict_to_driver(d) for d in raw['drivers']],
        sensors=[_dict_to_sensor(s) for s in raw['sensors']],
        laps_by_driver={
            int(idx): [_dict_to_lap(lap) for lap in laps]
            for idx, laps in raw['laps_by_driver'].items()
        },
    )


def _make_entry_factory(taken_slugs: set):
    """Closes over `taken_slugs`, which the engine guarantees is only ever touched
    from the event loop (make_entry never runs inside the threaded parse), so no
    locking is needed even with several files parsing concurrently.
    """
    def _make_entry(rel_path: str, parsed: _ParsedPngtFile, previous: Optional[PngtSessionEntry]) -> PngtSessionEntry:
        # A rename changes session_name (and therefore mtime, which is what forces
        # this file to be reparsed at all) -- but the slug must not follow it, per the
        # API spec's "Session Name vs Session ID" contract. Reusing the previous
        # entry's slug verbatim is what makes that hold once rename_session() lands in
        # a later commit; only a file with no previous entry gets a freshly computed one.
        if previous is not None:
            slug = previous.slug
        else:
            slug = _unique_slug(slugify(parsed.session.session_name), taken_slugs)
        taken_slugs.add(slug)
        return PngtSessionEntry(
            slug=slug,
            rel_path=rel_path,
            session=parsed.session,
            drivers=parsed.drivers,
            sensors=parsed.sensors,
            laps_by_driver=parsed.laps_by_driver,
        )
    return _make_entry


def make_pngt_handler() -> DiscoveryConfig:
    """Builds the .pngt handler to register with file_discovery.discover_all(),
    alongside whatever other file-type handlers a caller registers (e.g. a future
    JSON handler, once session_discovery.py is migrated onto this engine).

    Returns a *fresh* handler each call -- the slug-collision guard closes over its
    own `taken_slugs` set, which must start empty for each independent discovery run
    (e.g. each test, or each subsystem restart) rather than persist across runs.
    """
    taken_slugs: set = set()

    def _on_cache_loaded(known: Dict[str, PngtSessionEntry]) -> None:
        # Every already-assigned slug must be reserved before any new file's
        # collision check runs, not just the ones whose cache-hit happens to resolve
        # first -- see DiscoveryConfig.on_cache_loaded's docstring.
        taken_slugs.update(entry.slug for entry in known.values())

    return DiscoveryConfig[PngtSessionEntry](
        glob=_GLOB,
        cache_filename=CACHE_FILE,
        parse=_parse,
        make_entry=_make_entry_factory(taken_slugs),
        to_cache_dict=_entry_to_cache_dict,
        from_cache_dict=_cache_dict_to_entry,
        sort_key=lambda e: e.session.timestamp,
        on_cache_loaded=_on_cache_loaded,
        # Deliberately narrower than the engine's bare-Exception default: a real bug
        # in _parse/_make_entry (e.g. an AttributeError from a typo) should surface as
        # a crash during development, not get silently treated as "one bad file."
        catch=(PngtError, OSError, KeyError, ValueError),
    )


async def build_pngt_session_list(
    session_dir: Path,
    logger: PngLogger,
    app_version: str,
) -> AsyncIterator[Tuple[List[PngtSessionEntry], Dict[str, str]]]:
    """Standalone convenience wrapper for callers (tests, or a subsystem that only
    ever cares about pngt) that don't need the shared multi-handler walk -- registers
    just the pngt handler with discover_all() and adapts its output back to
    (entries, slug_map). A caller registering pngt alongside other handlers (e.g.
    web_server.py, once a second type exists) should call discover_all() directly
    with make_pngt_handler() in its handler list instead of this wrapper.
    """
    handler = make_pngt_handler()
    async for _handler, entries in discover_all(session_dir, logger, app_version, [handler]):
        slug_map = {e.slug: e.rel_path for e in entries}
        yield entries, slug_map
