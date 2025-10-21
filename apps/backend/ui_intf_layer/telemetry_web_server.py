# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
from typing import Any, Dict, Tuple

import apps.backend.state_mgmt_layer.intf as API
from apps.backend.state_mgmt_layer import SessionState
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.config import PngSettings
from lib.web_server import BaseWebServer

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class TelemetryWebServer(BaseWebServer):
    """
    A web server class for handling telemetry-related web services and socket communications.

    This class sets up HTTP and WebSocket routes for serving telemetry data,
    static files, and managing client connections.

    Attributes:
        m_port (int): The port number on which the server will run.
        m_debug_mode (bool): Flag to enable/disable debug mode.
        m_app (Quart): The Quart web application instance.
        m_sio (socketio.AsyncServer): The Socket.IO server instance.
        m_sio_app (socketio.ASGIApp): The combined Quart and Socket.IO ASGI application.
        m_ver_str (str): The version string.
        m_logger (logging.Logger): The logger instance.
    """

    def __init__(self,
                 settings: PngSettings,
                 ver_str: str,
                 logger: logging.Logger,
                 session_state: SessionState,
                 debug_mode: bool = False):
        """
        Initialize the TelemetryWebServer.

        Args:
            settings (PngSettings): App settings.
            ver_str (str): The version string.
            logger (logging.Logger): The logger instance.
            session_state (SessionState): Handle to the session state
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        super().__init__(
            port=settings.Network.server_port,
            ver_str=ver_str,
            logger=logger,
            cert_path=settings.HTTPS.cert_path,
            key_path=settings.HTTPS.key_path,
            disable_browser_autoload=settings.Display.disable_browser_autoload,
            debug_mode=debug_mode)
        self.define_routes()
        self.register_post_start_callback(self._post_start)
        self.m_show_start_sample_data = settings.StreamOverlay.show_sample_data_at_start
        self.m_session_state: SessionState = session_state

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
        async def index() -> str:
            """
            Render the main index page.

            Returns:
                str: Rendered HTML content for the index page.
            """
            return await self.render_template('driver-view.html', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/eng-view')
        async def engineerView() -> str:
            """
            Render the engineer view page.

            Returns:
                str: Rendered HTML content for the stream overlay page.
            """
            return await self.render_template('eng-view.html', live_data_mode=True, version=self.m_ver_str)

        @self.http_route('/player-stream-overlay')
        async def playerStreamOverlay() -> str:
            """
            Render the player stream overlay page.

            Returns:
                str: Rendered HTML content for the stream overlay page.
            """
            return await self.render_template('player-stream-overlay.html')

    def _defineDataRoutes(self) -> None:
        """
        Define HTTP routes for retrieving telemetry and race-related data.

        Sets up endpoints for fetching race info, telemetry info,
        driver info, and stream overlay info.
        """
        @self.http_route('/telemetry-info')
        async def telemetryInfoHTTP() -> Tuple[str, int]:
            """
            Provide telemetry information via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return API.PeriodicUpdateData(self.m_logger, self.m_session_state).toJSON(), HTTPStatus.OK

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple[str, int]:
            """
            Provide overall race statistics via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return API.RaceInfoData(self.m_logger, self.m_session_state).toJSON(), HTTPStatus.OK

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple[str, int]:
            """
            Provide driver information based on the index parameter.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return self._processDriverInfoRequest(self.request.args.get('index'))

        @self.http_route('/stream-overlay-info')
        async def streamOverlayInfoHTTP() -> Tuple[str, int]:
            """
            Provide stream overlay telemetry information via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return API.StreamOverlayData(self.m_session_state).toJSON(self.m_show_start_sample_data), HTTPStatus.OK

    def _processDriverInfoRequest(self, index_arg: Any) -> Tuple[Dict[str, Any], HTTPStatus]:
        """
        Process driver info request.

        Args:
            index_arg (Any): The index parameter, expected to be a number.

        Returns:
            Tuple[Dict[str, Any], HTTPStatus]: The response and HTTP status code.
        """

        # Validate the input
        if error_response := self.validate_int_get_request_param(index_arg, 'index'):
            return error_response, HTTPStatus.BAD_REQUEST

        # Check if the given index is valid
        index_int = int(index_arg)
        if not self.m_session_state.isIndexValid(index_int):
            error_response = {
                'error' : 'Invalid parameter value',
                'message' : 'Invalid index',
                'index' : index_arg
            }
            return self.jsonify(error_response), HTTPStatus.NOT_FOUND

        # Process parameters and generate response
        return API.DriverInfoRsp(self.m_session_state, index_int).toJSON(), HTTPStatus.OK

    async def _post_start(self) -> None:
        """Function to be called after the server starts serving."""
        proto = 'https' if self.m_cert_path else 'http'
        webbrowser.open(f'{proto}://localhost:{self.m_port}', new=2)
        notify_parent_init_complete()
