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

import asyncio
import errno
import logging
import socket
import webbrowser
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import socketio
import uvicorn
from quart import Quart, jsonify, render_template, request, send_from_directory

import apps.backend.state_mgmt_layer as TelState
from lib.error_status import PngPortInUseError
from lib.child_proc_mgmt import notify_parent_init_complete

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class TelemetryWebServer:
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
        self.m_logger: logging.Logger = logger
        self.m_port: int = port
        self.m_ver_str = ver_str
        self.m_cert_path: Optional[str] = cert_path
        self.m_key_path: Optional[str] = key_path
        self.m_disable_browser_autoload: bool = disable_browser_autoload
        self.m_debug_mode: bool = debug_mode
        self._shutdown_event = asyncio.Event()

        # Create a Quart app and Socket.IO server instance

        self.m_base_dir = Path(__file__).resolve().parent.parent.parent.parent
        template_dir = self.m_base_dir / "apps" / "frontend" / "html"
        static_dir = self.m_base_dir / "apps" / "frontend"
        self.m_app: Quart = Quart(
            __name__,
            template_folder=template_dir,
            static_folder=static_dir,
            static_url_path='/static'
        )
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = False

        self.m_sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False
        )
        self.m_sio_app: socketio.ASGIApp = socketio.ASGIApp(self.m_sio, self.m_app)

        # Define routes and socket handlers
        self.define_routes()
        self.define_socketio_handlers()

    def define_routes(self) -> None:
        """
        Define all HTTP routes for the web server.

        This method calls sub-methods to set up file and data routes.
        """

        @self.m_app.before_serving
        async def before_serving() -> None:
            """Function to be called before the server starts serving."""
            self.m_logger.debug("In post init ...")
            if not self.m_disable_browser_autoload:
                proto = 'https' if self.m_cert_path else 'http'
                webbrowser.open(f'{proto}://localhost:{self.m_port}', new=2)
            notify_parent_init_complete()

        self._defineFileRoutes()
        self._defineDataRoutes()

    def _defineFileRoutes(self) -> None:
        """
        Define routes for serving static and template files.

        Calls methods to set up static file and template routes.
        """
        self._defineStaticFileRoutes()
        self._defineTemplateFileRoutes()

    def _defineStaticFileRoutes(self) -> None:
        """
        Define routes for serving static files like icons and favicon.

        Uses a centralized dictionary to manage static file routes with
        their corresponding file paths and MIME types.
        """
        # Static routes dictionary remains the same as in the original code
        static_routes = {
            '/favicon.ico': {
                'file': 'favicon.ico',
                'mimetype': 'image/vnd.microsoft.icon'
            },
            '/tyre-icons/soft.svg': {
                'file': 'tyre-icons/soft_tyre.svg',
                'mimetype': 'image/svg+xml'
            },
            '/tyre-icons/super-soft.svg': {
                'file': 'tyre-icons/super_soft_tyre.svg',
                'mimetype': 'image/svg+xml'
            },
            '/tyre-icons/medium.svg': {
                'file': 'tyre-icons/medium_tyre.svg',
                'mimetype': 'image/svg+xml'
            },
            '/tyre-icons/hard.svg': {
                'file': 'tyre-icons/hard_tyre.svg',
                'mimetype': 'image/svg+xml'
            },
            '/tyre-icons/intermediate.svg': {
                'file': 'tyre-icons/intermediate_tyre.svg',
                'mimetype': 'image/svg+xml'
            },
            '/tyre-icons/wet.svg': {
                'file': 'tyre-icons/wet_tyre.svg',
                'mimetype': 'image/svg+xml'
            }
        }

        # Determine the absolute path to the static directory
        assets_dir = self.m_base_dir / "assets"

        # Dynamically create route handlers for each static file
        for route, config in static_routes.items():
            def make_static_route_handler(route_path: str, file_path: str, mime_type: str):
                """
                Create a route handler for a specific static file.

                Args:
                    route_path (str): The URL route for the file.
                    file_path (str): The path to the file within the static directory.
                    mime_type (str): The MIME type of the file.

                Returns:
                    Callable: An async function to serve the static file.
                """
                async def _static_route():
                    return await send_from_directory(assets_dir, file_path, mimetype=mime_type)

                _static_route.__name__ = f'serve_static_{route_path.replace("/", "_")}'
                return _static_route

            route_handler = make_static_route_handler(route, config['file'], config['mimetype'])
            self.m_app.route(route)(route_handler)

    def _defineTemplateFileRoutes(self) -> None:
        """
        Define routes for rendering HTML templates.

        Sets up routes for the main index page and stream overlay page.
        """
        @self.m_app.route('/')
        async def index() -> str:
            """
            Render the main index page.

            Returns:
                str: Rendered HTML content for the index page.
            """
            return await render_template('driver-view.html', live_data_mode=True, version=self.m_ver_str)

        @self.m_app.route('/eng-view')
        async def engineerView() -> str:
            """
            Render the player stream overlay page.

            Returns:
                str: Rendered HTML content for the stream overlay page.
            """
            return await render_template('eng-view.html')

        @self.m_app.route('/player-stream-overlay')
        async def playerStreamOverlay() -> str:
            """
            Render the player stream overlay page.

            Returns:
                str: Rendered HTML content for the stream overlay page.
            """
            return await render_template('player-stream-overlay.html')

    def _defineDataRoutes(self) -> None:
        """
        Define HTTP routes for retrieving telemetry and race-related data.

        Sets up endpoints for fetching race info, telemetry info,
        driver info, and stream overlay info.
        """
        @self.m_app.route('/telemetry-info')
        async def telemetryInfoHTTP() -> Tuple[str, int]:
            """
            Provide telemetry information via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return TelState.RaceInfoUpdate().toJSON(), HTTPStatus.OK

        @self.m_app.route('/race-info')
        async def raceInfoHTTP() -> Tuple[str, int]:
            """
            Provide overall race statistics via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return TelState.OverallRaceStatsRsp().toJSON(), HTTPStatus.OK

        @self.m_app.route('/driver-info')
        async def driverInfoHTTP() -> Tuple[str, int]:
            """
            Provide driver information based on the index parameter.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return self._processDriverInfoRequest(request.args.get('index'))

        @self.m_app.route('/stream-overlay-info')
        async def streamOverlayInfoHTTP() -> Tuple[str, int]:
            """
            Provide stream overlay telemetry information via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return TelState.PlayerTelemetryOverlayUpdate().toJSON(), HTTPStatus.OK

    def define_socketio_handlers(self) -> None:
        """
        Define Socket.IO event handlers for client management endpoints.
        """
        self._defineClientManagementEndpoints()

    def _defineClientManagementEndpoints(self) -> None:
        """
        Set up Socket.IO event handlers for client connection and registration.
        """
        # pylint: disable=unused-argument
        @self.m_sio.event
        async def connect(sid: str, environ: Dict[str, Any]) -> None:
            """
            Handle client connection event.

            Args:
                sid (str): Session ID of the connected client.
                environ (Dict[str, Any]): Environment information for the connection.
            """
            self.m_logger.debug("Client connected: %s", sid)

        @self.m_sio.event
        async def disconnect(sid: str) -> None:
            """
            Handle client disconnection event.

            Args:
                sid (str): Session ID of the disconnected client.
            """
            self.m_logger.debug("Client disconnected: %s", sid)

        @self.m_sio.on('register-client')
        async def handleClientRegistration(sid: str, data: Dict[str, str]) -> None:
            """
            Handle client registration for specific client types.

            Args:
                sid (str): Session ID of the registering client.
                data (Dict[str, str]): Registration data containing client type.
            """
            self.m_logger.debug('Client registered. SID = %s Type = %s', sid, data['type'])
            if (client_type := data['type']) in {'player-stream-overlay', 'race-table'}:
                await self.m_sio.enter_room(sid, client_type)
                if self.m_debug_mode:
                    self.m_logger.debug('Client %s joined room %s', sid, client_type)

                    room = self.m_sio.manager.rooms.get('/', {}).get(client_type)
                    self.m_logger.debug(f'Current members of {client_type}: {room}')

    def _validateIntGetRequestParam(self, param: Any, param_name: str) -> Optional[Dict[str, Any]]:
        """
        Validate integer get request parameter.

        Args:
            param (Any): The parameter to check.
            param_name (str) : The name of the parameter (used in response)

        Returns:
            Optional[Dict[str, Any]]: Error response if the parameter is invalid, else None.
        """

        # Check if only one parameter is provided
        if param is None:
            return {
                'error': 'Invalid parameters',
                'message': f'Provide "{param_name}" parameter'
            }

        # Check if the provided value for index is numeric
        if not isinstance(param, int) and not str(param).isdigit():
            return {
                'error': 'Invalid parameter value',
                'message': f'"{param_name}" parameter must be numeric'
            }

        return None

    def _processDriverInfoRequest(self, index_arg: Any) -> Tuple[Dict[str, Any], HTTPStatus]:
        """
        Process driver info request.

        Args:
            index_arg (Any): The index parameter, expected to be a number.

        Returns:
            Tuple[Dict[str, Any], HTTPStatus]: The response and HTTP status code.
        """

        # Validate the input
        if error_response := self._validateIntGetRequestParam(index_arg, 'index'):
            return error_response, HTTPStatus.BAD_REQUEST

        # Check if the given index is valid
        index_int = int(index_arg)
        if not TelState.isDriverIndexValid(index_int):
            error_response = {
                'error' : 'Invalid parameter value',
                'message' : 'Invalid index',
                'index' : index_arg
            }
            return jsonify(error_response), HTTPStatus.NOT_FOUND

        # Process parameters and generate response
        return TelState.DriverInfoRsp(index_int).toJSON(), HTTPStatus.OK


    async def run(self) -> None:
        """
        Run the web server asynchronously using Uvicorn.

        Sets up the server configuration and starts serving the application.
        """

        if not _is_port_available(self.m_port):
            self.m_logger.error(f"Port {self.m_port} is already in use")
            raise PngPortInUseError()

        # Create a socket manually to set SO_REUSEADDR
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("0.0.0.0", self.m_port))
        sock.listen(1024)
        sock.setblocking(False)

        config = uvicorn.Config(
            self.m_sio_app,
            log_level="warning",
            ssl_certfile=self.m_cert_path,
            ssl_keyfile=self.m_key_path,
        )

        server = uvicorn.Server(config)
        await server.serve(sockets=[sock])

    async def stop(self) -> None:
        """Stop the web server."""
        self._shutdown_event.set()

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _is_port_available(port: int) -> bool:
    """Check if a TCP port is available by trying to connect to it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', port))
        return result != 0  # returns True if port is not in use
