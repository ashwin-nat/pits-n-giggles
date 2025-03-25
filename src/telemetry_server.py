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
import os
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import socketio
# pylint: disable=unused-import
from engineio.async_drivers import gevent
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart, jsonify, render_template, request, send_from_directory

import src.telemetry_data as TelData
import src.telemetry_web_api as TelWebAPI
from lib.inter_thread_communicator import InterThreadCommunicator
from src.png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_web_server : Optional["TelemetryWebServer"] = None
png_logger = getLogger()
_race_table_clients : Set[str] = set()
_player_overlay_clients : Set[str] = set()

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
    """

    def __init__(self, port: int, debug_mode: bool = False):
        """
        Initialize the TelemetryWebServer.

        Args:
            port (int): The port number to run the server on.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        self.m_port: int = port
        self.m_debug_mode: bool = debug_mode
        self.subtasks: List[Tuple[Callable, Tuple[Any, ...]]] = []

        # Create a Quart app and Socket.IO server instance
        self.m_app: Quart = Quart(
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static'
        )
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = False

        self.m_sio: socketio.AsyncServer = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
        self.m_sio_app: socketio.ASGIApp = socketio.ASGIApp(self.m_sio, self.m_app)

        # Define routes and socket handlers
        self.define_routes()
        self.define_socketio_handlers()

    def define_routes(self) -> None:
        """
        Define all HTTP routes for the web server.

        This method calls sub-methods to set up file and data routes.
        """
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(current_dir, 'static')

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
                    return await send_from_directory(static_dir, file_path, mimetype=mime_type)

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
            return await render_template('index.html', live_data_mode=True)

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
            return TelWebAPI.RaceInfoUpdate().toJSON(), HTTPStatus.OK

        @self.m_app.route('/race-info')
        async def raceInfoHTTP() -> Tuple[str, int]:
            """
            Provide overall race statistics via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return TelWebAPI.OverallRaceStatsRsp().toJSON(), HTTPStatus.OK

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
            return TelWebAPI.PlayerTelemetryOverlayUpdate().toJSON(), HTTPStatus.OK

    def define_socketio_handlers(self) -> None:
        """
        Define Socket.IO event handlers for client management and data endpoints.
        """
        self._defineClientManagementEndpoints()
        self._defineDataEndpoints()

    def _defineClientManagementEndpoints(self) -> None:
        """
        Set up Socket.IO event handlers for client connection and registration.
        """
        @self.m_sio.event
        async def connect(sid: str, environ: Dict[str, Any]) -> None:
            """
            Handle client connection event.

            Args:
                sid (str): Session ID of the connected client.
                environ (Dict[str, Any]): Environment information for the connection.
            """
            png_logger.debug("Client connected: %s", sid)

        @self.m_sio.event
        async def disconnect(sid: str) -> None:
            """
            Handle client disconnection event.

            Args:
                sid (str): Session ID of the disconnected client.
            """
            png_logger.debug("Client disconnected: %s", sid)

        @self.m_sio.on('register-client')
        async def handleClientRegistration(sid: str, data: Dict[str, str]) -> None:
            """
            Handle client registration for specific client types.

            Args:
                sid (str): Session ID of the registering client.
                data (Dict[str, str]): Registration data containing client type.
            """
            png_logger.debug('Client registered. SID = %s Type = %s', sid, data['type'])
            if data['type'] == 'player-stream-overlay':
                _player_overlay_clients.add(sid)
            elif data['type'] == 'race-table':
                _race_table_clients.add(sid)

    def _defineDataEndpoints(self) -> None:
        """
        Set up Socket.IO event handlers for data-related events.
        """
        @self.m_sio.on('race-info')
        async def raceInfoSIO(sid: str, data: Dict[str, Any]) -> None:
            """
            Handle race info request via Socket.IO.

            Args:
                sid (str): Session ID of the requesting client.
                data (Dict[str, Any]): Request data, potentially including a dummy payload.
            """
            response = TelWebAPI.OverallRaceStatsRsp().toJSON()

            # Re-attach the dummy payload if present
            if "__dummy" in data:
                response["__dummy"] = data
            await self.m_sio.emit("race-info-response", response, to=sid)

        @self.m_sio.on('driver-info')
        async def driverInfoSIO(sid: str, data: Dict[str, Any]) -> None:
            """
            Handle driver info request via Socket.IO.

            Args:
                sid (str): Session ID of the requesting client.
                data (Dict[str, Any]): Request data with driver index and optional dummy payload.
            """
            response, _ = self._processDriverInfoRequest(data.get("index"))

            # Re-attach the dummy payload if present
            dummy_payload = data.get("__dummy")
            if dummy_payload:
                response["__dummy"] = dummy_payload
            await self.m_sio.emit("driver-info-response", response, to=sid)

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
        error_response = self._validateIntGetRequestParam(index_arg, 'index')
        if error_response:
            return error_response, HTTPStatus.BAD_REQUEST

        # Check if the given index is valid
        index_int = int(index_arg)
        if not TelData.isDriverIndexValid(index_int):
            error_response = {
                'error' : 'Invalid parameter value',
                'message' : 'Invalid index',
                'index' : index_arg
            }
            return jsonify(error_response), HTTPStatus.BAD_REQUEST

        # Process parameters and generate response
        return TelWebAPI.DriverInfoRsp(index_int).toJSON(), HTTPStatus.OK

    async def run(self) -> None:
        """
        Run the web server asynchronously.

        Sets up the server configuration and starts serving the application.
        """
        config = Config()
        config.bind = [f"0.0.0.0:{self.m_port}"]
        await serve(self.m_sio_app, config)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initTelemetryWebServer(
    port: int,
    client_update_interval_ms: int,
    debug_mode: bool,
    stream_overlay_start_sample_data: bool,
    tasks: List[asyncio.Task]) -> TelemetryWebServer:
    """Initialize the web server

    Args:
        port (int): Port number
        client_update_interval_ms (int): How often the client will be updated with new info
        debug_mode (bool): Debug enabled if true
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives

    Returns:
        TelemetryWebServer: The initialized web server
    """

    # First, create the server instance
    global _web_server
    _web_server = TelemetryWebServer(
        port=port,
        debug_mode=debug_mode,
    )

    # Register tasks associated with this server
    tasks.append(asyncio.create_task(_web_server.run(), name="Web Server Task"))
    tasks.append(asyncio.create_task(raceTableClientUpdateTask(client_update_interval_ms, _web_server.m_sio),
                                     name="Race Table Update Task"))
    tasks.append(asyncio.create_task(streamOverlayUpdateTask(60, stream_overlay_start_sample_data, _web_server.m_sio),
                                     name="Stream Overlay Update Task"))
    tasks.append(asyncio.create_task(frontEndMessageTask(1000, _web_server.m_sio),
                                     name="Front End Message Task"))
    return _web_server

async def raceTableClientUpdateTask(update_interval_ms: int, sio: socketio.AsyncServer) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
        sio (socketio.AsyncServer): The socketio server instance
    """

    global _web_server
    global _race_table_clients
    sleep_duration = update_interval_ms / 1000
    while True:
        if len(_race_table_clients) > 0:
            await sio.emit('race-table-update', TelWebAPI.RaceInfoUpdate().toJSON())
        await asyncio.sleep(sleep_duration)

async def streamOverlayUpdateTask(
    update_interval_ms: int,
    stream_overlay_start_sample_data: bool,
    sio: socketio.AsyncServer) -> None:
    """Task to update clients with player telemetry overlay data
    Args:
        update_interval_ms (int): Update interval in milliseconds
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        sio (socketio.AsyncServer): The socketio server instance
    """

    global _web_server
    global _player_overlay_clients
    sleep_duration = update_interval_ms / 1000
    while True:
        if len(_player_overlay_clients) > 0:
            await sio.emit('player-overlay-update',
                                        TelWebAPI.PlayerTelemetryOverlayUpdate()
                                            .toJSON(stream_overlay_start_sample_data))
        await asyncio.sleep(sleep_duration)

async def frontEndMessageTask(update_interval_ms: int, sio: socketio.AsyncServer) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
        sio (socketio.AsyncServer): The socketio server instance
    """

    sleep_duration = update_interval_ms / 1000
    while True:
        message = InterThreadCommunicator().receive("frontend-update")
        if message:
            png_logger.debug(f"Received stream update button press {str(message)}")
            await sio.emit('frontend-update', message.toJSON())
        await asyncio.sleep(sleep_duration)
