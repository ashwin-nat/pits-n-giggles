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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import time
import webbrowser
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from quart import send_file, url_for
from watchfiles import awatch

from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import PngSettings
from lib.ipc import IpcDealerAsync, PngAppId
from lib.logger import PngLogger
from lib.web_server import BaseWebServer, ClientType

from .session_discovery import build_session_list, CACHE_FILE, formula_group_key

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_DRIVER_INFO_HTTP_STATUS = {
    "MISSING_PARAM": HTTPStatus.BAD_REQUEST,
    "INVALID_PARAM": HTTPStatus.BAD_REQUEST,
    "NOT_FOUND":      HTTPStatus.NOT_FOUND,
}

def _best(sessions: List[Dict[str, Any]], key: str) -> float:
    vals = [s[key] for s in sessions if s.get(key, 0) > 0]
    return min(vals) if vals else 0

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WebServer(BaseWebServer):
    """
    Web server for the unified live dashboard. Blindly forwards broker telemetry to browser
    Socket.IO clients on its own cadence and bridges `/driver-info` + `/race-info` to the backend
    over the router/dealer channel.
    """

    def __init__(self,
                 settings: PngSettings,
                 ver_str: str,
                 logger: PngLogger,
                 session_dir: Path,
                 viewer_dir: Path,
                 debug_mode: bool = False):
        """
        Initialize the WebServer.

        Args:
            settings (PngSettings): App settings.
            ver_str (str): The version string.
            logger (PngLogger): The logger instance.
            session_dir (Path): Directory to scan for saved session JSON files.
            viewer_dir (Path): Directory containing the built f1-save-viewer React app.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        super().__init__(
            port=settings.Network.server_port,
            ver_str=ver_str,
            logger=logger,
            bind_address=settings.Network.bind_address,
            client_event_mappings={
                ClientType.RACE_TABLE: ['frontend-update', 'race-table-update'],
                ClientType.PLAYER_STREAM_OVERLAY: ['stream-overlay-update'],
            },
            cert_path=settings.HTTPS.cert_path,
            key_path=settings.HTTPS.key_path,
            debug_mode=debug_mode)
        self.m_dealer: Optional[IpcDealerAsync] = None
        self.m_race_table_cache: Optional[Dict[str, Any]] = None
        self.m_stream_overlay_cache: Optional[Dict[str, Any]] = None
        self.m_disable_browser_autoload = settings.Display.disable_browser_autoload

        self.m_session_dir: Path = session_dir
        self.m_viewer_dir: Path = viewer_dir
        self.m_sessions_cache: List[Dict[str, Any]] = []
        self.m_slug_map: Dict[str, str] = {}
        self._m_cache_ready = asyncio.Event()
        self._m_watch_stop = asyncio.Event()

        self.define_routes()
        self.register_post_start_callback(self._post_start)

    def set_dealer(self, dealer: IpcDealerAsync) -> None:
        """Attach the router/dealer client used to bridge `/driver-info` and `/race-info`."""
        self.m_dealer = dealer

    def update_race_table_cache(self, data: Dict[str, Any]) -> None:
        """Cache the latest `race-table-update` payload from the broker."""
        self.m_race_table_cache = data

    def update_stream_overlay_cache(self, data: Dict[str, Any]) -> None:
        """Cache the latest `stream-overlay-update` payload from the broker."""
        self.m_stream_overlay_cache = data

    def define_routes(self) -> None:
        """Define all HTTP routes for the web server."""
        self._defineTemplateFileRoutes()
        self._defineDataRoutes()
        self._defineSaveViewerRoutes()

    def _defineTemplateFileRoutes(self) -> None:
        """Define routes for rendering HTML templates."""

        @self.http_route('/')
        async def homeView() -> str:
            return await self.render_template('home.html', active_page='home', version=self.m_ver_str)

        @self.http_route('/live')
        async def liveView() -> str:
            return await self.render_template(
                'driver-view.html', active_page='live', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/eng-view')
        async def engineerView() -> str:
            return await self.render_template(
                'eng-view.html', active_page='eng-view', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/eng-view/trackmap')
        async def engineerViewTrackmap() -> str:
            return await self.render_template('eng-view-trackmap.html', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/player-stream-overlay')
        async def playerStreamOverlay() -> str:
            return await self.render_template('player-stream-overlay.html')

    def _defineDataRoutes(self) -> None:
        """Define HTTP routes for retrieving telemetry and race-related data."""

        @self.http_route('/telemetry-info')
        async def telemetryInfoHTTP() -> Tuple[Dict[str, Any], int]:
            return (self.m_race_table_cache or {}), HTTPStatus.OK

        @self.http_route('/stream-overlay-info')
        async def streamOverlayInfoHTTP() -> Tuple[Dict[str, Any], int]:
            return (self.m_stream_overlay_cache or {}), HTTPStatus.OK

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple[Dict[str, Any], int]:
            rsp = await self.m_dealer.request(str(PngAppId.BACKEND), "race-info-request", {})
            if rsp.get("status") == "error":
                return {'error': rsp.get("reason", "backend unavailable")}, HTTPStatus.SERVICE_UNAVAILABLE
            return rsp, HTTPStatus.OK

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple[Dict[str, Any], int]:
            index = self.request.args.get('index')
            rsp = await self.m_dealer.request(str(PngAppId.BACKEND), "driver-info-request", {"index": index})
            if rsp.get("status") == "error":
                return {'error': rsp.get("reason", "backend unavailable")}, HTTPStatus.SERVICE_UNAVAILABLE
            if rsp.get("ok"):
                return rsp["data"], HTTPStatus.OK
            http_status = _DRIVER_INFO_HTTP_STATUS.get(rsp.get("error_code"), HTTPStatus.BAD_REQUEST)
            return {'error': rsp.get("error")}, http_status

    async def _render_index(self) -> Any:
        """Read the built React index.html and inject the app version, the shared sidebar
        stylesheet, and the sidebar markup itself (React's own `<aside>` becomes the secondary
        rail alongside it).

        Returns:
            A Quart-compatible (body, status, headers) tuple serving index.html.
        """
        index_path = self.m_viewer_dir / 'index.html'
        html = index_path.read_text(encoding='utf-8')

        version_injection = f'<script>window.__PNG_VERSION__="{self.m_ver_str}";</script>'
        sidebar_css_url = url_for('static', filename='css/sidebar.css')
        head_injection = f'<link rel="stylesheet" href="{sidebar_css_url}">{version_injection}'
        html = html.replace('</head>', f'{head_injection}</head>', 1)

        sidebar_html = await self.render_template('partials/sidebar.html', active_page='save-viewer')
        sidebar_js_url = url_for('static', filename='js/sidebar.js')
        html = html.replace('<body class="', '<body class="png-has-sidebar ', 1)
        html = html.replace('<div id="root">', f'{sidebar_html}<div id="root">', 1)
        html = html.replace('</body>', f'<script src="{sidebar_js_url}"></script></body>', 1)

        return html, HTTPStatus.OK, {'Content-Type': 'text/html; charset=utf-8'}

    def _defineSaveViewerRoutes(self) -> None:
        """Define routes serving the React save-viewer SPA under /save-viewer/*."""

        @self.http_route('/save-viewer/')
        async def saveViewerIndex():
            return await self._render_index()

        @self.http_route('/save-viewer/<path:path>')
        async def saveViewerStatic(path: str):
            # Serve real static assets directly; fall back to index.html for any
            # unknown path so the client-side (React) router can resolve it.
            # Without this, refreshing/deep-linking a virtual route (e.g.
            # /save-viewer/f1-26/sessions/<slug>) would 404 since no such file exists on disk.
            # Resolve before checking existence: an unresolved is_file() on a "../"-laden
            # path would leak a file-existence oracle for the whole filesystem via the
            # 200 (found) vs 200-with-index (not found) response difference.
            root = self.m_viewer_dir.resolve()
            candidate = (root / path).resolve()
            if candidate.is_relative_to(root) and candidate.is_file():
                return await self.send_from_directory(self.m_viewer_dir, path)
            return await self._render_index()

        @self.http_route('/save-viewer/api/sessions')
        async def apiSessions():
            self.m_logger.debug("Received request for session list")
            await self._m_cache_ready.wait()
            self.m_logger.debug("GET /save-viewer/api/sessions -> %d sessions", len(self.m_sessions_cache))
            return self.jsonify(self.m_sessions_cache), HTTPStatus.OK

        @self.http_route('/save-viewer/api/sessions/<slug>')
        async def apiSession(slug: str):
            await self._m_cache_ready.wait()
            relative = self.m_slug_map.get(slug)
            if not relative:
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            root = self.m_session_dir.resolve()
            full = (root / relative).resolve()
            if not full.is_relative_to(root):
                return {'error': 'Forbidden'}, HTTPStatus.FORBIDDEN
            if not full.exists():
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            self.m_logger.debug("GET /save-viewer/api/sessions/%s -> %s", slug, full)
            return await send_file(full, mimetype='application/json')

        @self.http_route('/save-viewer/api/track-pbs')
        async def apiTrackPbs():
            track = self.request.args.get('track', '')
            formula_param = self.request.args.get('formula', '')
            exclude_slug = self.request.args.get('exclude', '')
            if not track:
                return {'error': 'Missing "track" parameter'}, HTTPStatus.BAD_REQUEST
            await self._m_cache_ready.wait()
            target_formula = formula_group_key(formula_param)
            track_sessions = [
                s for s in self.m_sessions_cache
                if s.get('track') == track
                and formula_group_key(s.get('formula', '')) == target_formula
                and s.get('slug') != exclude_slug
            ]
            return self.jsonify({
                'bestQualiLapMs': _best(track_sessions, 'bestLapTimeMs'),
                'bestS1Ms': _best(track_sessions, 'bestS1Ms'),
                'bestS2Ms': _best(track_sessions, 'bestS2Ms'),
                'bestS3Ms': _best(track_sessions, 'bestS3Ms'),
                'bestRaceLapMs': _best(track_sessions, 'bestRaceLapMs'),
                'bestRacePaceMs': _best(track_sessions, 'bestRacePaceMs'),
                'sessionCount': len(track_sessions),
            }), HTTPStatus.OK

    async def _rebuild_session_cache(self) -> None:
        """Rebuild session cache from disk, publishing partial results after each batch."""
        try:
            self.m_logger.debug("Session cache: scanning %s", self.m_session_dir)
            if not self.m_session_dir.exists():
                self.m_logger.warning("Session directory does not exist: %s", self.m_session_dir)
                return
            t0 = time.perf_counter()
            async for sessions, slug_map in build_session_list(self.m_session_dir, self.m_logger):
                self.m_sessions_cache = sessions
                self.m_slug_map = slug_map
                self._m_cache_ready.set()  # unblocks waiting requests after the first batch
            self.m_logger.info(
                "Session cache: loaded %d sessions in %.2fs",
                len(self.m_sessions_cache), time.perf_counter() - t0,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            self.m_logger.exception("Session cache: error building cache")
        finally:
            self._m_cache_ready.set()  # always unblock even if the directory was empty

    async def _sessions_watch_loop(self) -> None:
        """Background task: rebuild session cache whenever watchfiles detects a change."""
        if not self.m_session_dir.exists():
            self.m_logger.warning(
                "Session directory %s does not exist -- file watcher not started", self.m_session_dir)
            return
        async for _ in awatch(self.m_session_dir, stop_event=self._m_watch_stop,
                              watch_filter=lambda _, p: not p.endswith(CACHE_FILE)):
            try:
                await self._rebuild_session_cache()
            except Exception:  # pylint: disable=broad-exception-caught
                self.m_logger.exception("Error refreshing session cache")

    async def _post_start(self) -> None:
        """Function to be called after the server starts serving."""
        notify_parent_init_complete()

        @self.m_app.after_serving
        async def _stop_watch_loop() -> None:
            self._m_watch_stop.set()
            self.m_logger.info("Session watch loop stop signal sent")

        asyncio.create_task(self._rebuild_session_cache(), name="Session Initial Scan")
        asyncio.create_task(self._sessions_watch_loop(), name="Session Watch Loop")

        if not self.m_disable_browser_autoload:
            proto = 'https' if self.m_cert_path else 'http'
            webbrowser.open(f'{proto}://localhost:{self.m_port}', new=2)
