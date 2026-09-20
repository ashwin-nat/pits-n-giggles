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
import webbrowser
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from lib.config import AutoOpenDashboardMode, PngSettings
from lib.ipc import IpcDealerAsync
from lib.logger import PngLogger
from lib.subsystem.identity import PngSubsysId
from lib.web_server import BaseWebServer, ClientType

from .lap_analyzer_routes import (define_lap_analyzer_routes,
                                  init_lap_analyzer_routes,
                                  lap_analyzer_watch_loop,
                                  rebuild_lap_analyzer_cache,
                                  stop_lap_analyzer_watch_loop)
from .save_viewer_routes import (define_save_viewer_routes, get_slug_map,
                                 init_save_viewer_routes, rebuild_session_cache,
                                 sessions_watch_loop, stop_save_viewer_watch_loop,
                                 wait_for_session_cache)
from .save_viewer_state import (getDriverInfoFrom, getRaceInfoFrom,
                                getTelemetryInfoFrom, init_state)
from .session_discovery import load_session_json

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_DRIVER_INFO_HTTP_STATUS = {
    "MISSING_PARAM": HTTPStatus.BAD_REQUEST,
    "INVALID_PARAM": HTTPStatus.BAD_REQUEST,
    "NOT_FOUND":      HTTPStatus.NOT_FOUND,
}

_AUTO_OPEN_DASHBOARD_PATHS = {
    AutoOpenDashboardMode.HUB: '/',
    AutoOpenDashboardMode.DRIVER_VIEW: '/live',
    AutoOpenDashboardMode.ENGINEER_VIEW: '/eng-view',
    AutoOpenDashboardMode.SAVE_VIEW: '/save-viewer/',
}

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
                 analyzer_dir: Path,
                 on_ready: Callable[[], None],
                 debug_mode: bool = False):
        """
        Initialize the WebServer.

        Args:
            settings (PngSettings): App settings.
            ver_str (str): The version string.
            logger (PngLogger): The logger instance.
            session_dir (Path): Directory to scan for saved session JSON files.
            viewer_dir (Path): Directory containing the built f1-save-viewer React app.
            analyzer_dir (Path): Directory containing the built lap-analyzer React app.
            on_ready (Callable[[], None]): Called once the server is actually listening. This
                subsystem is only genuinely up at that point, not when it finishes constructing, so
                it owns the timing of the init-complete token.
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
        self.m_on_ready: Callable[[], None] = on_ready
        self.m_dealer: Optional[IpcDealerAsync] = None
        self.m_race_table_cache: Optional[Dict[str, Any]] = None
        self.m_stream_overlay_cache: Optional[Dict[str, Any]] = None
        self.m_auto_open_dashboard = settings.Display.auto_open_dashboard
        self.m_save_viewer_poll_interval_secs = settings.Display.save_viewer_poll_interval_secs

        self.m_session_dir: Path = session_dir
        # Holds every background task spawned via _spawn_background_task() below, for
        # exactly as long as it takes to keep asyncio from garbage-collecting a Task
        # nothing else references (the event loop itself only holds a weak one) --
        # see that method's docstring for why this can't go through add_task() yet.
        self._m_background_tasks: set = set()

        # save_viewer_routes.py / lap_analyzer_routes.py each own their route
        # family's cache/watch state at module level (see each module's docstring
        # for why) -- this is the one config value save-viewer's module needs
        # handed to it before any route can fire.
        init_save_viewer_routes(viewer_dir)
        init_lap_analyzer_routes(analyzer_dir)

        init_state(logger)
        self.define_routes()
        self.register_post_start_callback(self._post_start)

    def _spawn_background_task(self, coro: Any, name: str) -> None:
        """asyncio.create_task() wrapper that actually keeps the Task alive -- see
        the asyncio docs' own warning that a Task with no held reference can be
        garbage-collected mid-execution. No cleanup on completion: this is called
        exactly 4 times total for the lifetime of the process (twice from
        _post_start, which only ever runs once), not a per-request/repeated-spawn
        pattern, so the set never grows past 4 -- discarding finished entries would
        just be extra code for a leak that can't happen here.

        TODO: migrate to the subsystem's add_task() once it supports registering
        work mid-event-loop-run (planned). It doesn't today: AsyncSubsystem._async_main()
        snapshots its task list into a local `started` and gathers *that* once, before
        this class's _post_start() ever runs (which fires from deep inside one of
        those already-gathered tasks, once Quart actually begins serving) -- a
        SubsystemTask registered that late would never be started.
        """
        task = asyncio.create_task(coro, name=name)
        self._m_background_tasks.add(task)

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
        define_save_viewer_routes(self)
        define_lap_analyzer_routes(self)

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

        @self.http_route('/legacy/<slug>')
        async def legacyView(slug: str) -> Any:
            await wait_for_session_cache()
            if not get_slug_map().get(slug):
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            return await self.render_template(
                'driver-view.html', live_data_mode=False, version=self.m_ver_str, session_slug=slug
            )

    def _defineDataRoutes(self) -> None:
        """Define HTTP routes for retrieving telemetry and race-related data.

        Each route also serves saved-session data via an optional `?slug=` query param
        (used by the `/legacy/<slug>` driver-view, reading a session JSON file from disk
        instead of the live broker cache).
        """

        @self.http_route('/telemetry-info')
        async def telemetryInfoHTTP() -> Tuple[Dict[str, Any], int]:
            slug = self.request.args.get('slug')
            if not slug:
                return (self.m_race_table_cache or {}), HTTPStatus.OK
            data = await load_session_json(self.m_session_dir, get_slug_map(), slug)
            if data is None:
                return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
            return getTelemetryInfoFrom(data), HTTPStatus.OK

        @self.http_route('/stream-overlay-info')
        async def streamOverlayInfoHTTP() -> Tuple[Dict[str, Any], int]:
            return (self.m_stream_overlay_cache or {}), HTTPStatus.OK

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple[Dict[str, Any], int]:
            slug = self.request.args.get('slug')
            if slug:
                data = await load_session_json(self.m_session_dir, get_slug_map(), slug)
                if data is None:
                    return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
                return getRaceInfoFrom(data), HTTPStatus.OK
            rsp = await self.m_dealer.request(str(PngSubsysId.BACKEND), "race-info-request", {})
            if rsp.get("status") == "error":
                return {'error': rsp.get("reason", "backend unavailable")}, HTTPStatus.SERVICE_UNAVAILABLE
            return rsp, HTTPStatus.OK

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple[Dict[str, Any], int]:
            index = self.request.args.get('index')
            slug = self.request.args.get('slug')
            if slug:
                if not index or not index.isdigit():
                    return {'error': 'Invalid parameter value', 'message': '"index" parameter must be numeric'}, \
                        HTTPStatus.BAD_REQUEST
                data = await load_session_json(self.m_session_dir, get_slug_map(), slug)
                if data is None:
                    return {'error': 'Session not found'}, HTTPStatus.NOT_FOUND
                if driver_info := getDriverInfoFrom(data, int(index)):
                    return driver_info, HTTPStatus.OK
                return {'error': 'Invalid parameter value', 'message': 'Invalid index'}, HTTPStatus.NOT_FOUND
            rsp = await self.m_dealer.request(str(PngSubsysId.BACKEND), "driver-info-request", {"index": index})
            if rsp.get("status") == "error":
                return {'error': rsp.get("reason", "backend unavailable")}, HTTPStatus.SERVICE_UNAVAILABLE
            if rsp.get("ok"):
                return rsp["data"], HTTPStatus.OK
            http_status = _DRIVER_INFO_HTTP_STATUS.get(rsp.get("error_code"), HTTPStatus.BAD_REQUEST)
            return {'error': rsp.get("error")}, http_status

    async def _post_start(self) -> None:
        """Function to be called after the server starts serving."""
        self.m_on_ready()

        @self.m_app.after_serving
        async def _stop_watch_loop() -> None:
            stop_save_viewer_watch_loop()
            stop_lap_analyzer_watch_loop()
            self.m_logger.info("Session watch loop stop signal sent")

        self._spawn_background_task(rebuild_session_cache(self), name="Session Initial Scan")
        self._spawn_background_task(sessions_watch_loop(self), name="Session Watch Loop")
        self._spawn_background_task(rebuild_lap_analyzer_cache(self), name="Lap Analyzer Initial Scan")
        self._spawn_background_task(lap_analyzer_watch_loop(self), name="Lap Analyzer Watch Loop")

        if self.m_auto_open_dashboard != AutoOpenDashboardMode.DISABLED:
            proto = 'https' if self.m_cert_path else 'http'
            path = _AUTO_OPEN_DASHBOARD_PATHS[self.m_auto_open_dashboard]
            webbrowser.open(f'{proto}://localhost:{self.m_port}{path}', new=2)
