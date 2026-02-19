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
import logging
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple

import apps.save_viewer.save_viewer_state as SaveViewerState
from lib.child_proc_mgmt import notify_parent_init_complete
from lib.event_counter import EventCounter
from lib.web_server import BaseWebServer, ClientType

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
                 logger: logging.Logger,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None,
                 debug_mode: bool = False):
        """
        Initialize the TelemetryWebServer.

        Args:
            port (int): The port number to run the server on.
            ver_str (str): The version string.
            logger (logging.Logger): The logger instance.
            cert_path (Optional[str], optional): Path to the certificate file. Defaults to None.
            key_path (Optional[str], optional): Path to the key file. Defaults to None.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        super().__init__(port, ver_str, logger, cert_path, key_path, debug_mode)
        self.m_stats = EventCounter()
        self.define_routes()
        self.register_post_start_callback(self._post_start)
        self.register_on_client_register_callback(self._on_client_connect)
        self.register_on_client_disconnect_callback(self._on_client_disconnect)

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
            self.m_stats.track("__HTTP__", "/", 0)
            return await self.render_template('driver-view.html', live_data_mode=False, version=self.m_ver_str)

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
            self.m_stats.track("__HTTP__", "/telemetry-info", 0)
            return SaveViewerState.getTelemetryInfo()

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple[str, int]:
            """
            Provide overall race statistics via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            self.m_stats.track("__HTTP__", "/race-info", 0)
            return SaveViewerState.getRaceInfo()

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple[str, int]:
            """
            Provide driver information based on the index parameter.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """

            self.m_stats.track("__HTTP__", "/driver-info", 0)
            index: str = self.request.args.get('index')

            # Check if only one parameter is provided
            if not index:
                error_response = {
                    'error': 'Invalid parameters',
                    'message': 'Provide "index" parameter'
                }
                return error_response, HTTPStatus.BAD_REQUEST

            # Check if the provided value for index is numeric
            if not index.isdigit():
                error_response = {
                    'error': 'Invalid parameter value',
                    'message': '"index" parameter must be numeric'
                }
                return error_response, HTTPStatus.BAD_REQUEST

            # Process parameters and generate response
            index_int = int(index)

            if driver_info := SaveViewerState.getDriverInfo(index_int):
                return driver_info, HTTPStatus.OK
            error_response = {
                'error' : 'Invalid parameter value',
                'message' : 'Invalid index'
            }
            return error_response, HTTPStatus.NOT_FOUND

    async def _post_start(self) -> None:
        """
        Notify the parent process that the web server is initialized.
        """
        notify_parent_init_complete()

    async def _on_client_connect(self, client_type: ClientType, client_id: str) -> None:
        """Send race table to the newly connected client

        Args:
            client_type (ClientType): Client type
            client_id (str): Client ID
        """
        self.m_stats.track("__SOCKET_IN__", "__CONNECT__", 0)
        self.m_stats.track("__SOCKET_IN__", f"__CONNECT__{str(client_type)}", 0)
        if client_type == ClientType.RACE_TABLE:
            await self._send_race_table(client_id)

    async def _on_client_disconnect(self, _sid: str) -> None:
        """Called when a client disconnects
        """
        self.m_stats.track("__SOCKET_IN__", "__DISCONNECT__", 0)

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
        self.m_stats.track("__SOCKET_OUT__", event, 0)
        await super().send_to_clients_of_type(event, data, client_type)

    async def send_to_clients_interested_in_event(self, event: str, data: Dict[str, Any]) -> None:
        self.m_stats.track("__SOCKET_OUT__", event, 0)
        await super().send_to_clients_interested_in_event(event, data)

    async def send_to_client(self, event: str, data: Dict[str, Any], client_id: str) -> None:
        self.m_stats.track("__SOCKET_OUT__", event, 0)
        await super().send_to_client(event, data, client_id)

    def get_stats(self) -> dict:
        """Get current web server stats."""
        return self.m_stats.get_stats()

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_server_task(port: int, ver_str: str, logger: logging.Logger, tasks: List[asyncio.Task]) -> SaveViewerWebServer:
    """Initialize the web server and return the server object for proper cleanup

    Args:
        port (int): Port number
        ver_str (str): Version string
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks to be executed

    Returns:
        SaveViewerWebServer: Web server
    """
    _server = SaveViewerWebServer(port, ver_str, logger)
    tasks.append(asyncio.create_task(_server.run(), name="Web Server Task"))
    return _server
