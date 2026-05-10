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
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List, Optional

from quart import redirect, send_file
from watchfiles import awatch

import apps.save_viewer.save_viewer_state as SaveViewerState
from apps.save_viewer.session_discovery import CACHE_FILE, build_session_list, formula_group_key, load_session_json
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.logger import PngLogger
from lib.web_server import BaseWebServer, ClientType

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _best(sessions: List[Dict[str, Any]], key: str) -> float:
    vals = [s[key] for s in sessions if s.get(key, 0) > 0]
    return min(vals) if vals else 0

# -------------------------------------- CLASSES ----------------------------------------------------------------

class SaveViewerWebServer(BaseWebServer):
    """
    A web server class for handling telemetry-related web services and socket communications.

    This class sets up HTTP and WebSocket routes for serving telemetry data,
    static files, and managing client connections.
    """

    def __init__(self,
                 port: int,
                 ver_str: str,
                 logger: PngLogger,
                 bind_address: str,
                 session_dir: Path,
                 viewer_dir: Path,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None,
                 debug_mode: bool = False):
        """
        Initialize the TelemetryWebServer.

        Args:
            port (int): The port number to run the server on.
            ver_str (str): The version string.
            logger (PngLogger): The logger instance.
            bind_address (str): IP address to bind the server to.
            session_dir (Path): Directory to scan for saved session JSON files.
            viewer_dir (Path): Directory containing the built f1-save-viewer React app.
            cert_path (Optional[str], optional): Path to the certificate file. Defaults to None.
            key_path (Optional[str], optional): Path to the key file. Defaults to None.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        self.m_session_dir: Path = session_dir
        self.m_viewer_dir: Path = viewer_dir
        self.m_sessions_cache: List[Dict[str, Any]] = []
        self.m_slug_map: Dict[str, str] = {}
        self._m_cache_ready = asyncio.Event()
        self._m_watch_stop = asyncio.Event()
        super().__init__(port, ver_str, logger,
                         bind_address=bind_address,
                         cert_path=cert_path,
                         key_path=key_path,
                         debug_mode=debug_mode,
                         enable_socketio=False)
        self.define_routes()
        self.register_post_start_callback(self._post_start)
        self.register_on_client_register_callback(self._on_client_connect)

    def define_routes(self) -> None:
        """
        Define all HTTP routes for the web server.

        This method calls sub-methods to set up file and data routes.
        """

        self._defineTemplateFileRoutes()
        self._defineDataRoutes()

    def _defineTemplateFileRoutes(self) -> None:
        """
        Define routes for rendering HTML templates.

        Sets up routes for the main index page and stream overlay page.
        """
        @self.http_route('/')
        async def index():
            return redirect('/viewer/')

        @self.http_route('/viewer/')
        async def viewerIndex():
            index_path = self.m_viewer_dir / 'index.html'
            html = index_path.read_text(encoding='utf-8')
            injection = f'<script>window.__PNG_VERSION__="{self.m_ver_str}";</script>'
            html = html.replace('</head>', f'{injection}</head>', 1)
            return html, HTTPStatus.OK, {'Content-Type': 'text/html; charset=utf-8'}

        @self.http_route('/viewer/<path:path>')
        async def viewerStatic(path: str):
            return await self.send_from_directory(self.m_viewer_dir, path)

        @self.http_route('/legacy/<slug>')
        async def legacyView(slug: str):
            if not self.m_slug_map:
                async for sessions, slug_map in build_session_list(self.m_session_dir, self.m_logger):
                    self.m_sessions_cache = sessions
                    self.m_slug_map = slug_map
            if not self.m_slug_map.get(slug):
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            return await self.render_template(
                'driver-view.html', live_data_mode=False, version=self.m_ver_str, session_slug=slug
            )

    def _defineDataRoutes(self) -> None:
        """
        Define HTTP routes for retrieving telemetry and race-related data.

        Sets up endpoints for fetching race info, telemetry info,
        driver info, and stream overlay info.
        """
        @self.http_route('/api/sessions')
        async def apiSessions():
            self.m_logger.info("Received request for session list")
            await self._m_cache_ready.wait()
            self.m_logger.info("GET /api/sessions → %d sessions", len(self.m_sessions_cache))
            return self.jsonify(self.m_sessions_cache), HTTPStatus.OK

        @self.http_route('/api/sessions/<slug>')
        async def apiSession(slug: str):
            relative = self.m_slug_map.get(slug)
            if not relative:
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            root = self.m_session_dir.resolve()
            full = (root / relative).resolve()
            if not full.is_relative_to(root):
                return {'error': 'Forbidden'}, HTTPStatus.FORBIDDEN
            if not full.exists():
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            self.m_logger.debug("GET /api/sessions/%s → %s", slug, full)
            return await send_file(full, mimetype='application/json')

        @self.http_route('/api/track-pbs')
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

        @self.http_route('/telemetry-info')
        async def telemetryInfoHTTP():
            slug = self.request.args.get('slug')
            if slug:
                data = load_session_json(self.m_session_dir, self.m_slug_map, slug)
                if data is None:
                    return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
                return SaveViewerState.getTelemetryInfoFrom(data), HTTPStatus.OK
            return SaveViewerState.getTelemetryInfo()

        @self.http_route('/race-info')
        async def raceInfoHTTP():
            slug = self.request.args.get('slug')
            if slug:
                data = load_session_json(self.m_session_dir, self.m_slug_map, slug)
                if data is None:
                    return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
                return SaveViewerState.getRaceInfoFrom(data), HTTPStatus.OK
            return SaveViewerState.getRaceInfo()

        @self.http_route('/driver-info')
        async def driverInfoHTTP():
            index: str = self.request.args.get('index')
            slug: str = self.request.args.get('slug')

            if not index:
                return {'error': 'Invalid parameters', 'message': 'Provide "index" parameter'}, HTTPStatus.BAD_REQUEST

            if not index.isdigit():
                return {'error': 'Invalid parameter value', 'message': '"index" parameter must be numeric'}, HTTPStatus.BAD_REQUEST

            index_int = int(index)
            if slug:
                data = load_session_json(self.m_session_dir, self.m_slug_map, slug)
                if data is None:
                    return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
                if driver_info := SaveViewerState.getDriverInfoFrom(data, index_int):
                    return driver_info, HTTPStatus.OK
                return {'error': 'Invalid parameter value', 'message': 'Invalid index'}, HTTPStatus.NOT_FOUND
            if driver_info := SaveViewerState.getDriverInfo(index_int):
                return driver_info, HTTPStatus.OK
            return {'error': 'Invalid parameter value', 'message': 'Invalid index'}, HTTPStatus.NOT_FOUND

    async def _rebuild_cache(self) -> None:
        """Rebuild session cache from disk, publishing partial results after each batch."""
        try:
            self.m_logger.info("Session cache: scanning %s", self.m_session_dir)
            if not self.m_session_dir.exists():
                self.m_logger.warning("Session directory does not exist: %s", self.m_session_dir)
                return
            t0 = time.perf_counter()
            async for sessions, slug_map in build_session_list(self.m_session_dir, self.m_logger):
                self.m_sessions_cache = sessions
                self.m_slug_map = slug_map
                self._m_cache_ready.set()  # unblocks waiting requests after the first batch
            self.m_logger.info(
                "Session cache: fully loaded %d sessions in %.2fs (dir: %s)",
                len(self.m_sessions_cache), time.perf_counter() - t0, self.m_session_dir,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            self.m_logger.exception("Session cache: error building cache")
        finally:
            self._m_cache_ready.set()  # always unblock even if the directory was empty

    async def _sessions_watch_loop(self) -> None:
        """Background task: rebuild session cache whenever watchfiles detects a change."""
        if not self.m_session_dir.exists():
            self.m_logger.warning("Session directory %s does not exist — file watcher not started", self.m_session_dir)
            return
        async for _ in awatch(self.m_session_dir, stop_event=self._m_watch_stop,
                              watch_filter=lambda _, p: not p.endswith(CACHE_FILE)):
            try:
                await self._rebuild_cache()
            except Exception:  # pylint: disable=broad-exception-caught
                self.m_logger.exception("Error refreshing session cache")

    async def _post_start(self) -> None:
        """Notify the parent process that the web server is initialized and start session watcher."""
        notify_parent_init_complete()

        @self.m_app.after_serving
        async def _stop_watch_loop() -> None:
            self._m_watch_stop.set()
            self.m_logger.info("Session watch loop stop signal sent")

        asyncio.create_task(self._rebuild_cache(), name="Session Initial Scan")
        asyncio.create_task(self._sessions_watch_loop(), name="Session Watch Loop")

    async def _on_client_connect(self, client_type: ClientType, client_id: str) -> None:
        """Send race table to the newly connected client

        Args:
            client_type (ClientType): Client type
            client_id (str): Client ID
        """
        if client_type == ClientType.RACE_TABLE:
            await self._send_race_table(client_id)

    async def _send_race_table(self, client_id: str) -> None:
        """Send race table to all connected clients

        Args:
            client_id (str): Client ID
        """
        await self.send_to_client('race-table-update',
                                    SaveViewerState.getTelemetryInfo(),
                                    client_id)
        self.m_logger.debug("Sending race table update")

    async def send_to_clients_of_type(self, event: str, data: Dict[str, Any], client_type: ClientType) -> None:
        await super().send_to_clients_of_type(event, data, client_type)

    async def send_to_clients_interested_in_event(self, event: str, data: Dict[str, Any]) -> None:
        await super().send_to_clients_interested_in_event(event, data)

    async def send_to_client(self, event: str, data: Dict[str, Any], client_id: str) -> None:
        await super().send_to_client(event, data, client_id)

    def get_stats(self) -> dict:
        """Get current web server stats."""
        return self.m_stats.get_stats()

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_server_task(
    port: int,
    ver_str: str,
    logger: PngLogger,
    tasks: List[asyncio.Task],
    bind_address: str,
    session_dir: Path,
    viewer_dir: Path) -> SaveViewerWebServer:
    """Initialize the web server and return the server object for proper cleanup

    Args:
        port (int): Port number
        ver_str (str): Version string
        logger (PngLogger): Logger
        tasks (List[asyncio.Task]): List of tasks to be executed
        bind_address (str): IP address to bind the server to
        session_dir (Path): Directory to scan for saved session JSON files
        viewer_dir (Path): Directory containing the built f1-save-viewer React app

    Returns:
        SaveViewerWebServer: Web server
    """
    _server = SaveViewerWebServer(port, ver_str, logger, bind_address=bind_address,
                                  session_dir=session_dir, viewer_dir=viewer_dir)
    tasks.append(asyncio.create_task(_server.run(), name="Web Server Task"))
    return _server
