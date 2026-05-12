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

import logging
import webbrowser
from http import HTTPStatus
from typing import Dict, Optional, Tuple

from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import PngSettings
from lib.ipc import IpcDealerAsync, PngAppId
from lib.web_server import BaseWebServer, ClientType

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class TelemetryWebServer(BaseWebServer):
    """HTTP/Socket.IO server subprocess. Serves the frontend and proxies REST
    queries to the backend via IPC dealer. Live data is received from the broker
    via IpcSubscriberAsync (handled in ui_tasks) and cached here for REST."""

    def __init__(self,
                 settings: PngSettings,
                 ver_str: str,
                 logger: logging.Logger,
                 dealer: IpcDealerAsync,
                 debug_mode: bool = False):
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

        self.m_dealer: IpcDealerAsync = dealer
        self.m_disable_browser_autoload: bool = settings.Display.disable_browser_autoload
        self.m_last_race_table: Optional[Dict] = None
        self.m_last_stream_overlay: Optional[Dict] = None

        self.define_routes()
        self.register_post_start_callback(self._post_start)

    def define_routes(self) -> None:
        self._defineTemplateFileRoutes()
        self._defineDataRoutes()

    def _defineTemplateFileRoutes(self) -> None:
        @self.http_route('/')
        async def index() -> str:
            return await self.render_template('driver-view.html', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/eng-view')
        async def engineerView() -> str:
            return await self.render_template('eng-view.html', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/eng-view/trackmap')
        async def engineerViewTrackmap() -> str:
            return await self.render_template('eng-view-trackmap.html', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/player-stream-overlay')
        async def playerStreamOverlay() -> str:
            return await self.render_template('player-stream-overlay.html')

    def _defineDataRoutes(self) -> None:
        @self.http_route('/telemetry-info')
        async def telemetryInfoHTTP() -> Tuple:
            if self.m_last_race_table is None:
                return {'error': 'No data yet'}, HTTPStatus.SERVICE_UNAVAILABLE
            return self.m_last_race_table, HTTPStatus.OK

        @self.http_route('/stream-overlay-info')
        async def streamOverlayInfoHTTP() -> Tuple:
            if self.m_last_stream_overlay is None:
                return {'error': 'No data yet'}, HTTPStatus.SERVICE_UNAVAILABLE
            return self.m_last_stream_overlay, HTTPStatus.OK

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple:
            rsp = await self.m_dealer.send(str(PngAppId.BACKEND), "race-info-request", {})
            if rsp.get("ok"):
                return rsp["data"], HTTPStatus.OK
            return {'error': 'Backend unavailable'}, HTTPStatus.SERVICE_UNAVAILABLE

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple:
            index_arg = self.request.args.get('index')
            rsp = await self.m_dealer.send(
                str(PngAppId.BACKEND), "driver-info-request", {"index": index_arg}
            )
            if rsp.get("ok"):
                return rsp["data"], HTTPStatus.OK
            error = rsp.get("error", "unknown error")
            # Map backend error strings to HTTP status codes
            if "missing" in error.lower():
                return {'error': error}, HTTPStatus.BAD_REQUEST
            if "invalid" in error.lower():
                return {'error': error}, HTTPStatus.BAD_REQUEST
            return {'error': error}, HTTPStatus.NOT_FOUND

    # ------------------------------------------------------------------
    # Methods called by subscriber tasks to push data to clients
    # ------------------------------------------------------------------

    async def update_race_table(self, data: dict) -> None:
        """Cache latest race-table payload and emit to interested Socket.IO clients."""
        self.m_last_race_table = data
        if self.is_any_client_interested_in_event('race-table-update'):
            await self.send_to_clients_interested_in_event(event='race-table-update', data=data)

    async def update_stream_overlay(self, data: dict) -> None:
        """Cache latest stream-overlay payload and emit to interested Socket.IO clients."""
        self.m_last_stream_overlay = data
        if self.is_any_client_interested_in_event('stream-overlay-update'):
            await self.send_to_clients_interested_in_event(event='stream-overlay-update', data=data)

    async def push_frontend_update(self, data: dict) -> None:
        """Fan out a frontend-update event to RACE_TABLE clients."""
        await self.send_to_clients_of_type(
            event='frontend-update',
            data=data,
            client_type=ClientType.RACE_TABLE,
        )

    async def _post_start(self) -> None:
        notify_parent_init_complete()
        if not self.m_disable_browser_autoload:
            proto = 'https' if self.m_cert_path else 'http'
            webbrowser.open(f'{proto}://localhost:{self.m_port}', new=2)
