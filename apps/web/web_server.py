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

import webbrowser
from http import HTTPStatus
from typing import Any, Dict, Optional, Tuple

from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import PngSettings
from lib.ipc import IpcDealerAsync, PngAppId
from lib.logger import PngLogger
from lib.web_server import BaseWebServer, ClientType

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_DRIVER_INFO_HTTP_STATUS = {
    "MISSING_PARAM": HTTPStatus.BAD_REQUEST,
    "INVALID_PARAM": HTTPStatus.BAD_REQUEST,
    "NOT_FOUND":      HTTPStatus.NOT_FOUND,
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
                 debug_mode: bool = False):
        """
        Initialize the WebServer.

        Args:
            settings (PngSettings): App settings.
            ver_str (str): The version string.
            logger (PngLogger): The logger instance.
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

    def _defineTemplateFileRoutes(self) -> None:
        """Define routes for rendering HTML templates."""

        @self.http_route('/live')
        async def liveView() -> str:
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

    async def _post_start(self) -> None:
        """Function to be called after the server starts serving."""
        notify_parent_init_complete()
        if not self.m_disable_browser_autoload:
            proto = 'https' if self.m_cert_path else 'http'
            webbrowser.open(f'{proto}://localhost:{self.m_port}', new=2)
