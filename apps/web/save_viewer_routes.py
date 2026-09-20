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

"""The /save-viewer/* route family: serving the React save-viewer SPA and its JSON
save-data API. Split out of web_server.py -- route/task functions take the owning
`WebServer` instance as an explicit parameter for its capabilities (http_route,
jsonify, logger, ...), same idiom as `lib.subsystem`'s `AddTask`; not a mixin class.

This route family's own cache/watch state is module-level, not attached to the
WebServer instance: there is exactly one WebServer per process (one subsystem, one
instance for its lifetime), so instance-level storage here would only add
indirection with no real benefit. `init_save_viewer_routes()` sets `_viewer_dir`
once, during WebServer construction, before any route can fire.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import json
import time
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from quart import send_file, url_for
from watchfiles import awatch

from .pngt_discovery import CACHE_FILE as PNGT_CACHE_FILE
from .session_discovery import CACHE_FILE, build_session_list, formula_group_key

if TYPE_CHECKING:
    from .web_server import WebServer

# -------------------------------------- MODULE STATE --------------------------------------------------------------

_viewer_dir: Path = Path()
_sessions_cache: List[Dict[str, Any]] = []
_slug_map: Dict[str, str] = {}
_cache_ready = asyncio.Event()
_watch_stop = asyncio.Event()

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_save_viewer_routes(viewer_dir: Path) -> None:
    """Call once, during WebServer construction, before `define_save_viewer_routes()`
    and before scheduling `rebuild_session_cache()` / `sessions_watch_loop()`."""
    global _viewer_dir  # pylint: disable=global-statement
    _viewer_dir = viewer_dir


def stop_save_viewer_watch_loop() -> None:
    """Signal `sessions_watch_loop()` to stop -- called from WebServer's own
    `after_serving` shutdown hook. A function, not a bare module export, so
    web_server.py never reaches into this module's underscore-prefixed state
    directly (same reasoning as not injecting attributes onto WebServer)."""
    _watch_stop.set()


async def wait_for_session_cache() -> None:
    """Block until the first cache build (or an empty-directory no-op) completes.
    Used by web_server.py's own routes (e.g. `/legacy/<slug>`) that need the slug
    map before this module's own routes have necessarily been hit yet."""
    await _cache_ready.wait()


def get_slug_map() -> Dict[str, str]:
    """The current slug -> relative-path map. Read-only for callers outside this
    module; only `rebuild_session_cache()` ever reassigns it."""
    return _slug_map


def _best(sessions: List[Dict[str, Any]], key: str) -> float:
    vals = [s[key] for s in sessions if s.get(key, 0) > 0]
    return min(vals) if vals else 0


async def render_save_viewer_index(server: "WebServer") -> Any:
    """Read the built React index.html and inject the app version, the save-viewer
    runtime config, the shared sidebar stylesheet, and the sidebar markup itself
    (React's own `<aside>` becomes the secondary rail alongside it).

    Returns:
        A Quart-compatible (body, status, headers) tuple serving index.html.
    """
    index_path = _viewer_dir / 'index.html'
    html = index_path.read_text(encoding='utf-8')

    # Override the submodule's own bundled favicon/apple-touch-icon with ours, so the
    # browser tab shows the app logo consistently across every page instead of the
    # upstream save-viewer's own branding.
    html = html.replace('href="/save-viewer/favicon.ico"', 'href="/favicon.ico"', 1)
    html = html.replace('href="/save-viewer/apple-touch-icon.png"', 'href="/logo.png"', 1)

    version_injection = f'<script>window.__PNG_VERSION__="{server.m_ver_str}";</script>'
    poll_interval_ms = (
        server.m_save_viewer_poll_interval_secs * 1000
        if server.m_save_viewer_poll_interval_secs is not None
        else None
    )
    poll_interval_json = json.dumps(poll_interval_ms)
    save_viewer_config_injection = (
        f'<script>window.__PNG_SAVE_VIEWER_CONFIG__='
        f'{{"sessionPollIntervalMs":{poll_interval_json}}};</script>'
    )
    sidebar_css_url = url_for('static', filename='css/sidebar.css')
    bootstrap_icons_link = (
        '<link rel="stylesheet" '
        'href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" '
        'integrity="sha384-tViUnnbYAV00FLIhhi3v/dWt3Jxw4gZQcNoSCxCIFNJVCx7/D55/wXsrNIRANwdD" '
        'crossorigin="anonymous">'
    )
    head_injection = (
        f'{bootstrap_icons_link}<link rel="stylesheet" href="{sidebar_css_url}">'
        f'{version_injection}{save_viewer_config_injection}'
    )
    html = html.replace('</head>', f'{head_injection}</head>', 1)

    sidebar_html = await server.render_template('partials/sidebar.html', active_page='save-viewer')
    sidebar_js_url = url_for('static', filename='js/sidebar.js')
    html = html.replace('<body class="', '<body class="png-has-sidebar ', 1)
    html = html.replace('<div id="root">', f'{sidebar_html}<div id="root">', 1)
    html = html.replace('</body>', f'<script src="{sidebar_js_url}"></script></body>', 1)

    return html, HTTPStatus.OK, {'Content-Type': 'text/html; charset=utf-8'}


def define_save_viewer_routes(server: "WebServer") -> None:
    """Define routes serving the React save-viewer SPA under /save-viewer/*."""

    @server.http_route('/save-viewer/')
    async def saveViewerIndex():
        return await render_save_viewer_index(server)

    @server.http_route('/save-viewer/<path:path>')
    async def saveViewerStatic(path: str):
        # Serve real static assets directly; fall back to index.html for any
        # unknown path so the client-side (React) router can resolve it.
        # Without this, refreshing/deep-linking a virtual route (e.g.
        # /save-viewer/f1-26/sessions/<slug>) would 404 since no such file exists on disk.
        # Resolve before checking existence: an unresolved is_file() on a "../"-laden
        # path would leak a file-existence oracle for the whole filesystem via the
        # 200 (found) vs 200-with-index (not found) response difference.
        root = _viewer_dir.resolve()
        candidate = (root / path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return await server.send_from_directory(_viewer_dir, path)
        return await render_save_viewer_index(server)

    @server.http_route('/save-viewer/api/sessions')
    async def apiSessions():
        server.m_logger.debug("Received request for session list")
        await _cache_ready.wait()
        server.m_logger.debug("GET /save-viewer/api/sessions -> %d sessions", len(_sessions_cache))
        return server.jsonify(_sessions_cache), HTTPStatus.OK

    @server.http_route('/save-viewer/api/sessions/<slug>')
    async def apiSession(slug: str):
        await _cache_ready.wait()
        relative = _slug_map.get(slug)
        if not relative:
            return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
        root = server.m_session_dir.resolve()
        full = (root / relative).resolve()
        if not full.is_relative_to(root):
            return {'error': 'Forbidden'}, HTTPStatus.FORBIDDEN
        if not full.exists():
            return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
        server.m_logger.debug("GET /save-viewer/api/sessions/%s -> %s", slug, full)
        return await send_file(full, mimetype='application/json')

    @server.http_route('/save-viewer/api/track-pbs')
    async def apiTrackPbs():
        track = server.request.args.get('track', '')
        formula_param = server.request.args.get('formula', '')
        exclude_slug = server.request.args.get('exclude', '')
        if not track:
            return {'error': 'Missing "track" parameter'}, HTTPStatus.BAD_REQUEST
        await _cache_ready.wait()
        target_formula = formula_group_key(formula_param)
        track_sessions = [
            s for s in _sessions_cache
            if s.get('track') == track
            and formula_group_key(s.get('formula', '')) == target_formula
            and s.get('slug') != exclude_slug
        ]
        return server.jsonify({
            'bestQualiLapMs': _best(track_sessions, 'bestLapTimeMs'),
            'bestS1Ms': _best(track_sessions, 'bestS1Ms'),
            'bestS2Ms': _best(track_sessions, 'bestS2Ms'),
            'bestS3Ms': _best(track_sessions, 'bestS3Ms'),
            'bestRaceLapMs': _best(track_sessions, 'bestRaceLapMs'),
            'bestRacePaceMs': _best(track_sessions, 'bestRacePaceMs'),
            'sessionCount': len(track_sessions),
        }), HTTPStatus.OK


async def rebuild_session_cache(server: "WebServer") -> None:
    """Rebuild session cache from disk, publishing partial results after each batch."""
    global _sessions_cache, _slug_map  # pylint: disable=global-statement
    try:
        server.m_logger.debug("Session cache: scanning %s", server.m_session_dir)
        if not server.m_session_dir.exists():
            server.m_logger.warning("Session directory does not exist: %s", server.m_session_dir)
            return
        t0 = time.perf_counter()
        async for sessions, slug_map in build_session_list(server.m_session_dir, server.m_logger, server.m_ver_str):
            _sessions_cache = sessions
            _slug_map = slug_map
            _cache_ready.set()  # unblocks waiting requests after the first batch
        server.m_logger.info(
            "Session cache: loaded %d sessions in %.2fs",
            len(_sessions_cache), time.perf_counter() - t0,
        )
    except Exception:  # pylint: disable=broad-exception-caught
        server.m_logger.exception("Session cache: error building cache")
    finally:
        _cache_ready.set()  # always unblock even if the directory was empty


async def sessions_watch_loop(server: "WebServer") -> None:
    """Background task: rebuild session cache whenever watchfiles detects a change."""
    if not server.m_session_dir.exists():
        server.m_logger.warning(
            "Session directory %s does not exist -- file watcher not started", server.m_session_dir)
        return
    # Also ignores the pngt cache file and .pngt files themselves -- this watcher
    # only ever looks for *.json (see session_discovery.find_json_files), so a
    # telemetry recording finishing (or its own cache being rewritten) has nothing
    # for it to find and would otherwise trigger a wasted full rescan.
    async for _ in awatch(
            server.m_session_dir, stop_event=_watch_stop,
            watch_filter=lambda _, p: not p.endswith((CACHE_FILE, PNGT_CACHE_FILE, '.pngt'))):
        try:
            await rebuild_session_cache(server)
        except Exception:  # pylint: disable=broad-exception-caught
            server.m_logger.exception("Error refreshing session cache")
