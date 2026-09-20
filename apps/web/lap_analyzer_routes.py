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

"""The /lap-analyzer/api/v1/* route family: the telemetry visualizer's REST API,
serving .pngt recordings. Split out of web_server.py -- same free-function-taking-
the-owner-for-capabilities idiom as save_viewer_routes.py (see that module's
docstring); not a mixin.

This route family's own cache/watch state is module-level, not attached to the
WebServer instance -- same reasoning as save_viewer_routes.py: exactly one
WebServer exists per process, so there's nothing per-instance state would buy here.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import dataclasses
import time
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import ValidationError
from watchfiles import awatch

from lib.pngt import (DriverNotFoundError, PngtError, read_lap_telemetry,
                      rename_session)
from lib.track_segment_info import TrackSegmentsDatabase

from .lap_analyzer_api import (RenameSessionRequest, api_error, driver_to_api,
                               lap_to_api, session_to_api,
                               telemetry_points_to_api, track_section_to_api)
from .pngt_discovery import (CACHE_FILE, PngtSessionEntry,
                             build_pngt_session_list)
from .session_discovery import CACHE_FILE as JSON_CACHE_FILE

if TYPE_CHECKING:
    from .web_server import WebServer

# -------------------------------------- MODULE STATE --------------------------------------------------------------

_analyzer_dir: Path = Path()
_sessions_cache: List[PngtSessionEntry] = []
_by_slug: Dict[str, PngtSessionEntry] = {}
_cache_ready = asyncio.Event()
_watch_stop = asyncio.Event()

# Track segment data (assets/track-segments/*.json) is static and unrelated to any
# recorded session -- unlike the pngt cache above, it needs no watch loop and no
# readiness event. Built once at import time, same as session_state.py's own
# TrackSegmentsDatabase construction.
_track_segments_db = TrackSegmentsDatabase(Path(__file__).resolve().parents[2] / "assets" / "track-segments")

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_lap_analyzer_routes(analyzer_dir: Path) -> None:
    """Call once, during WebServer construction, before `define_lap_analyzer_routes()`
    -- same idiom as save_viewer_routes.init_save_viewer_routes()."""
    global _analyzer_dir  # pylint: disable=global-statement
    _analyzer_dir = analyzer_dir


def stop_lap_analyzer_watch_loop() -> None:
    """Signal `lap_analyzer_watch_loop()` to stop -- called from WebServer's own
    `after_serving` shutdown hook. A function, not a bare module export, so
    web_server.py never reaches into this module's underscore-prefixed state
    directly (same reasoning as not injecting attributes onto WebServer)."""
    _watch_stop.set()


class _TelemetryRequestError(Exception):
    """Raised by the validation helpers below to short-circuit
    apiLapAnalyzerTelemetry with a specific API error response -- caught once, at
    the top of the route handler, instead of a chain of early `return`s."""

    def __init__(self, code: str, message: str, status: HTTPStatus) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _resolve_telemetry_session(session_id: str) -> PngtSessionEntry:
    entry = _by_slug.get(session_id)
    if entry is None:
        raise _TelemetryRequestError(
            'SESSION_NOT_FOUND', f'Unknown session id: {session_id}', HTTPStatus.NOT_FOUND)
    return entry


def _check_telemetry_driver(entry: PngtSessionEntry, driver_index: int) -> None:
    driver = next((d for d in entry.drivers if d.driver_index == driver_index), None)
    if driver is None:
        raise _TelemetryRequestError(
            'DRIVER_NOT_FOUND', f'Driver {driver_index} not in session {entry.slug}', HTTPStatus.NOT_FOUND)
    if not driver.is_telemetry_public:
        raise _TelemetryRequestError(
            'TELEMETRY_RESTRICTED', f'Driver {driver_index} has restricted telemetry', HTTPStatus.FORBIDDEN)


def _resolve_telemetry_sensors(entry: PngtSessionEntry, sensors_param: str) -> List[str]:
    sensors = [s.strip() for s in sensors_param.split(',') if s.strip()]
    if not sensors:
        raise _TelemetryRequestError(
            'INVALID_SENSOR', 'sensors query parameter is required', HTTPStatus.BAD_REQUEST)
    manifest_keys = {s.key for s in entry.sensors}
    unknown = [s for s in sensors if s not in manifest_keys]
    if unknown:
        raise _TelemetryRequestError(
            'INVALID_SENSOR', f'Unknown sensor key(s) not in session manifest: {", ".join(unknown)}',
            HTTPStatus.BAD_REQUEST)
    return sensors


def _read_telemetry_arrays(
    server: "WebServer", entry: PngtSessionEntry, driver_index: int, lap_number: int,
) -> Dict[str, Any]:
    full_path = server.m_session_dir / entry.rel_path
    try:
        arrays = read_lap_telemetry(full_path, driver_index, lap_number)
    except DriverNotFoundError as exc:
        # read_lap_telemetry raises this for any missing drivers/{i}/lap_{n}.npz
        # entry, whether the driver or the lap number is what's actually wrong --
        # the driver is already validated by _check_telemetry_driver(), so at this
        # point it's the lap.
        raise _TelemetryRequestError(
            'LAP_NOT_FOUND', f'Lap {lap_number} not recorded for driver {driver_index}', HTTPStatus.NOT_FOUND
        ) from exc
    except PngtError as exc:
        server.m_logger.exception("Lap-analyzer telemetry: failed to read %s: %s", full_path, exc)
        raise _TelemetryRequestError(
            'INTERNAL_ERROR', 'Failed to read telemetry from the recording', HTTPStatus.INTERNAL_SERVER_ERROR
        ) from exc

    if arrays.get('lap_distance') is None:
        server.m_logger.error("Lap-analyzer telemetry: %s is missing its lap_distance array", full_path)
        raise _TelemetryRequestError(
            'INTERNAL_ERROR', 'Recorded lap is missing its lap_distance array', HTTPStatus.INTERNAL_SERVER_ERROR)
    return arrays


def _update_cached_session_name(session_id: str, new_name: str) -> None:
    """Patches the renamed session's name into both module-level cache structures
    in place, immediately -- see apiLapAnalyzerRenameSession's own comment for why
    this doesn't just wait for the watch loop to notice and rebuild."""
    global _sessions_cache, _by_slug  # pylint: disable=global-statement
    old_entry = _by_slug[session_id]
    new_entry = dataclasses.replace(old_entry, session=dataclasses.replace(
        old_entry.session, session_name=new_name))
    _sessions_cache = [new_entry if e.slug == session_id else e for e in _sessions_cache]
    _by_slug = {**_by_slug, session_id: new_entry}


def define_lap_analyzer_routes(server: "WebServer") -> None:
    """Define routes serving the lap-analyzer SPA under /lap-analyzer/* and its REST
    API under /lap-analyzer/api/v1/*. The API is read-only for now -- mark-good/
    delete are a later phase, per the write-API gate design in the API spec.
    """

    @server.http_route('/lap-analyzer/')
    async def lapAnalyzerIndex():
        return await server.send_from_directory(_analyzer_dir, 'index.html')

    @server.http_route('/lap-analyzer/<path:path>')
    async def lapAnalyzerStatic(path: str):
        # Serve a real built asset directly; fall back to index.html for any unknown
        # path so the client-side router can resolve it -- same reasoning and
        # traversal-safety check as save_viewer_routes.py's own static+fallback route.
        root = _analyzer_dir.resolve()
        candidate = (root / path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return await server.send_from_directory(_analyzer_dir, path)
        return await server.send_from_directory(_analyzer_dir, 'index.html')

    @server.http_route('/lap-analyzer/api/v1/sessions')
    async def apiLapAnalyzerSessions():
        await _cache_ready.wait()
        # "Sessions with no recorded laps are excluded" (API spec) -- laps_count is
        # the file's own authoritative total across all drivers, not recomputed here.
        sessions = [
            session_to_api(entry) for entry in _sessions_cache
            if entry.session.laps_count > 0
        ]
        return server.jsonify(sessions), HTTPStatus.OK

    @server.http_route('/lap-analyzer/api/v1/sessions/<session_id>/drivers')
    async def apiLapAnalyzerDrivers(session_id: str):
        await _cache_ready.wait()
        entry = _by_slug.get(session_id)
        if entry is None:
            return api_error('SESSION_NOT_FOUND',
                             f'Unknown session id: {session_id}'), HTTPStatus.NOT_FOUND
        return server.jsonify([driver_to_api(d) for d in entry.drivers]), HTTPStatus.OK

    @server.http_route('/lap-analyzer/api/v1/sessions/<session_id>/drivers/<int:driver_index>/laps')
    async def apiLapAnalyzerLaps(session_id: str, driver_index: int):
        await _cache_ready.wait()
        entry = _by_slug.get(session_id)
        if entry is None:
            return api_error('SESSION_NOT_FOUND',
                             f'Unknown session id: {session_id}'), HTTPStatus.NOT_FOUND
        if not any(d.driver_index == driver_index for d in entry.drivers):
            return api_error(
                'DRIVER_NOT_FOUND', f'Driver {driver_index} not in session {session_id}'
            ), HTTPStatus.NOT_FOUND
        # Restricted/scope-excluded drivers legitimately have no laps.json at all
        # (see file format spec) -- an empty list here is a normal response, not
        # an error, matching LocalFileProvider's getLaps() behaviour.
        laps = entry.laps_by_driver.get(driver_index, [])
        return server.jsonify([lap_to_api(lap) for lap in laps]), HTTPStatus.OK

    @server.http_route('/lap-analyzer/api/v1/telemetry/<session_id>/<int:driver_index>/<int:lap_number>')
    async def apiLapAnalyzerTelemetry(session_id: str, driver_index: int, lap_number: int):
        await _cache_ready.wait()
        try:
            entry = _resolve_telemetry_session(session_id)
            _check_telemetry_driver(entry, driver_index)
            sensors = _resolve_telemetry_sensors(entry, server.request.args.get('sensors', ''))
            arrays = _read_telemetry_arrays(server, entry, driver_index, lap_number)
            # TelemetryPoint stays a plain dict -- its keys are whichever sensors were
            # requested, a genuinely dynamic shape a fixed model wouldn't fit (see
            # lap_analyzer_api.py's module docstring). Stays inside this try block: a
            # per-sensor array shorter than lap_distance (e.g. a truncated recording)
            # raises IndexError here, which must still return the API's error
            # envelope, not Quart's default unstructured 500 page.
            points = telemetry_points_to_api(arrays['lap_distance'], arrays, sensors)
        except _TelemetryRequestError as exc:
            return api_error(exc.code, exc.message), exc.status
        except Exception as exc:  # pylint: disable=broad-exception-caught
            server.m_logger.exception(
                "Lap-analyzer telemetry: unexpected error building response for %s/%s/%s: %s",
                session_id, driver_index, lap_number, exc)
            return api_error(
                'INTERNAL_ERROR', 'Failed to build telemetry response'), HTTPStatus.INTERNAL_SERVER_ERROR

        return server.jsonify({
            'sessionId': session_id,
            'driverIndex': driver_index,
            'lapNumber': lap_number,
            'points': points,
        }), HTTPStatus.OK

    @server.http_route('/lap-analyzer/api/v1/tracks/<int:track_id>/sections')
    async def apiLapAnalyzerTrackSections(track_id: int):
        # No pngt cache wait -- track segment data is static and independent of any
        # recorded session. An unknown track_id returns 200 with an empty array,
        # not a 404, matching LocalFileProvider's getTrackSections() (see
        # lap_analyzer_api.track_section_to_api's docstring).
        track = _track_segments_db.get(track_id)
        sections = [track_section_to_api(seg) for seg in track.segments] if track is not None else []
        return server.jsonify(sections), HTTPStatus.OK

    @server.http_route('/lap-analyzer/api/v1/sessions/<session_id>/name', methods=['PATCH'])
    async def apiLapAnalyzerRenameSession(session_id: str):
        await _cache_ready.wait()
        entry = _by_slug.get(session_id)
        if entry is None:
            return api_error('SESSION_NOT_FOUND',
                             f'Unknown session id: {session_id}'), HTTPStatus.NOT_FOUND

        body = await server.request.get_json(silent=True)
        try:
            request = RenameSessionRequest.model_validate(body)
        except ValidationError as exc:
            message = "; ".join(e['msg'] for e in exc.errors())
            return api_error('INVALID_NAME', message), HTTPStatus.BAD_REQUEST
        new_name = request.name

        full_path = server.m_session_dir / entry.rel_path
        try:
            # rename_session() rewrites the whole zip archive on disk -- a blocking
            # call with no async equivalent, so it must not run directly on the
            # event loop (see BaseWebServer.run_blocking's own docstring).
            await server.run_blocking(rename_session, full_path, new_name)
        except PngtError as exc:
            server.m_logger.exception("Lap-analyzer rename: failed to rename %s: %s", full_path, exc)
            return api_error(
                'INTERNAL_ERROR', 'Failed to rename the recording'), HTTPStatus.INTERNAL_SERVER_ERROR

        # Patch the in-memory cache immediately, rather than waiting for the watch
        # loop to notice the rewrite's mtime bump and rebuild -- a GET /sessions
        # right after this response should already reflect the new name. The slug
        # (session_id/the dict key) never changes; only the entry's own session_name
        # does. The on-disk gzip cache is left to the watch loop to reconcile, same
        # as any other external edit to a .pngt file -- it's a startup-time
        # optimization, not this module's runtime source of truth.
        _update_cached_session_name(session_id, new_name)

        return server.jsonify({'id': session_id, 'name': new_name}), HTTPStatus.OK


async def rebuild_lap_analyzer_cache(server: "WebServer") -> None:
    """Rebuild the .pngt session cache from disk, publishing partial results after
    each file completes."""
    global _sessions_cache, _by_slug  # pylint: disable=global-statement
    try:
        server.m_logger.debug("Lap-analyzer cache: scanning %s", server.m_session_dir)
        if not server.m_session_dir.exists():
            server.m_logger.warning("Session directory does not exist: %s", server.m_session_dir)
            return
        t0 = time.perf_counter()
        async for sessions, _slug_map in build_pngt_session_list(
                server.m_session_dir, server.m_logger, server.m_ver_str):
            _sessions_cache = sessions
            _by_slug = {e.slug: e for e in sessions}
            _cache_ready.set()  # unblocks waiting requests after the first file
        server.m_logger.info(
            "Lap-analyzer cache: loaded %d sessions in %.2fs",
            len(_sessions_cache), time.perf_counter() - t0,
        )
    except Exception:  # pylint: disable=broad-exception-caught
        server.m_logger.exception("Lap-analyzer cache: error building cache")
    finally:
        _cache_ready.set()  # always unblock even if the directory was empty


async def lap_analyzer_watch_loop(server: "WebServer") -> None:
    """Background task: rebuild the .pngt cache whenever watchfiles detects a
    change. A separate watcher from sessions_watch_loop's, on the same directory --
    each must ignore the *other* format's cache file as well as its own, or the two
    watchers would keep re-triggering each other's rebuilds.
    """
    if not server.m_session_dir.exists():
        server.m_logger.warning(
            "Session directory %s does not exist -- lap-analyzer file watcher not started",
            server.m_session_dir)
        return
    async for _ in awatch(
            server.m_session_dir, stop_event=_watch_stop,
            watch_filter=lambda _, p: not p.endswith((CACHE_FILE, JSON_CACHE_FILE))):
        try:
            await rebuild_lap_analyzer_cache(server)
        except Exception:  # pylint: disable=broad-exception-caught
            server.m_logger.exception("Error refreshing lap-analyzer cache")
