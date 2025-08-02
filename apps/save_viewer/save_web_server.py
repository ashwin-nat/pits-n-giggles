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

from lib.web_server import ClientType, BaseWebServer
import logging
import asyncio
from typing import Optional, Tuple, List
from http import HTTPStatus

from lib.child_proc_mgmt import notify_parent_init_complete
import apps.save_viewer.save_viewer_state as SaveViewerState

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
                 disable_browser_autoload: bool = False,
                 debug_mode: bool = False):
        """
        Initialize the TelemetryWebServer.

        Args:
            port (int): The port number to run the server on.
            ver_str (str): The version string.
            logger (logging.Logger): The logger instance.
            cert_path (Optional[str], optional): Path to the certificate file. Defaults to None.
            key_path (Optional[str], optional): Path to the key file. Defaults to None.
            disable_browser_autoload (bool, optional): Whether to disable browser autoload. Defaults to False.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        super().__init__(port, ver_str, logger, cert_path, key_path, disable_browser_autoload, debug_mode)
        self.define_routes()
        self.register_post_start_callback(self._post_start)
        self.register_on_client_connect_callback(self._on_client_connect)

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
            return SaveViewerState.getTelemetryInfo()

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple[str, int]:
            """
            Provide overall race statistics via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return SaveViewerState.getRaceInfo()

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple[str, int]:
            """
            Provide driver information based on the index parameter.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """

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

    async def _on_client_connect(self, client_type: ClientType) -> None:
        """Send race table to the newly connected client"""
        if client_type == ClientType.RACE_TABLE:
            await self._send_race_table()

    async def _send_race_table(self) -> None:
        """Send race table to all connected clients"""
        await self.send_to_clients_of_type('race-table-update',
                                           SaveViewerState.getTelemetryInfo(),
                                           ClientType.RACE_TABLE)
        self.m_logger.debug("Sending race table update")

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
