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

import contextlib
import logging
import os
import platform
import socket
from pathlib import Path
from typing import Any, Awaitable, Callable, Coroutine, Dict, Optional, Union

import msgpack
import socketio
import uvicorn
import wsproto
from quart import Quart, Response
from quart import jsonify as quart_jsonify
from quart import render_template as quart_render_template
from quart import request as quart_request
from quart import send_from_directory as quart_send_from_directory
from quart import url_for

from lib.error_status import PngPortInUseError
from lib.port_check import is_port_available

from .client_types import ClientType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseWebServer:
    """Base class for a web server. Derived classes must implement their routes of interest"""
    def __init__(self,
                 port: int,
                 ver_str: str,
                 logger: logging.Logger,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None,
                 disable_browser_autoload: bool = False,
                 debug_mode: bool = False):
        """
        Initialize the BaseWebServer.

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
        self._post_start_callback: Optional[Callable[[], Awaitable[None]]] = None
        self._on_client_connect_callback: Optional[Callable[[ClientType, str], Awaitable[None]]] = None

        self.m_base_dir = Path(__file__).resolve().parent.parent.parent
        template_dir = self.m_base_dir / "apps" / "frontend" / "html"
        static_dir = self.m_base_dir / "apps" / "frontend"
        self.m_logger.debug("Base directory: %s", self.m_base_dir)
        self.m_logger.debug("Template directory: %s", template_dir)
        self.m_logger.debug("Static directory: %s", static_dir)
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
        self._server: Optional[uvicorn.Server] = None

        self._register_base_socketio_events()
        self._define_static_file_routes()

        # Automatically append version string to all static URL's
        # We're doing this because when version changes, we don't want the browser to load cached code
        #    as the code may have changed in the update. When the browser sees a new version appended as arg,
        #    it will actually request from the server, since the request is now different than what it has seen before
        @self.m_app.context_processor
        def override_url_for():
            def dated_url_for(endpoint, **values):
                if endpoint == 'static':
                    values['v'] = self.m_ver_str
                return url_for(endpoint, **values)
            return {"url_for": dated_url_for}

        # Disable caching for template paths, always.
        @self.m_app.after_request
        async def no_html_cache(response: Response) -> Response:
            # Only apply to HTML responses
            if response.content_type and response.content_type.startswith("text/html"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response

    def http_route(self, path: str, **kwargs) -> Callable:
        """Register a HTTP route."""
        def decorator(func: Callable[..., Coroutine]) -> Callable:
            self.m_app.route(path, **kwargs)(func)
            return func
        return decorator

    def socketio_event(self, event: str) -> Callable:
        """Register a SocketIO event."""
        def decorator(func: Callable[..., Coroutine]) -> Callable:
            self.m_sio.on(event)(func)
            return func
        return decorator

    def _register_base_socketio_events(self) -> None:
        """Register base SocketIO events."""

        @self.m_sio.event
        async def connect(sid: str, _environ: Dict[str, Any]) -> None:
            """
            Handle client connection event.

            Args:
                sid (str): Session ID of the connected client.
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
            self.m_logger.debug('Client registered. SID = %s Type = %s ID=%s', sid, data['type'], data.get('id', 'N/A'))
            if (client_type := data['type']) in {'player-stream-overlay', 'race-table'}:
                await self.m_sio.enter_room(sid, client_type)
                if self._on_client_connect_callback:
                    await self._on_client_connect_callback(ClientType(client_type), sid)
                if self.m_debug_mode:
                    self.m_logger.debug('Client %s joined room %s', sid, client_type)

                    room = self.m_sio.manager.rooms.get('/', {}).get(client_type)
                    self.m_logger.debug(f'Current members of {client_type}: {room}')

    async def send_to_clients_of_type(self, event: str, data: Dict[str, Any], client_type: ClientType) -> None:
        """
        Send data to clients in a specific room.

        Args:
            event (str): The event name to send.
            data (Dict[str, Any]): The data to send with the event.
            client_type (ClientType): The client type to send the event to.
        """
        packed = msgpack.packb(data, use_bin_type=True)
        await self.m_sio.emit(event, packed, room=str(client_type))

    async def send_to_client(self, event: str, data: Dict[str, Any], client_id: str) -> None:
        """
        Send data to clients in a specific room.

        Args:
            event (str): The event name to send.
            data (Dict[str, Any]): The data to send with the event.
            client_id (str): The client ID to send the event to.
        """
        packed = msgpack.packb(data, use_bin_type=True)
        await self.m_sio.emit(event, packed, to=client_id)

    def is_client_of_type_connected(self, client_type: ClientType) -> bool:
        """Check if a client of a specific type is connected

        Args:
            client_type (ClientType): The client type to check

        Returns:
            bool: True if a client of the specified type is connected
        """
        return self._is_room_empty(str(client_type))

    def _is_room_empty(self, room_name: str, namespace: Optional[str] = '/') -> bool:
        """Check if a room is empty"""
        participants = list(self.m_sio.manager.get_participants(namespace, room_name))
        return not participants

    async def run(self) -> None:
        """
        Run the web server asynchronously using Uvicorn.

        Sets up the server configuration and starts serving the application.
        """

        if not is_port_available(self.m_port):
            self.m_logger.error(f"Port {self.m_port} is already in use")
            raise PngPortInUseError()

        # Register post start callback before running
        @self.m_app.before_serving
        async def before_serving() -> None:
            self.m_logger.debug("In post init ...")
            if self._post_start_callback:
                await self._post_start_callback()

        # Create a socket manually to set SO_REUSEADDR
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if platform.system() != "Windows":
            with contextlib.suppress(AttributeError, OSError):
                # pylint: disable=useless-suppression
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) # pylint: disable=no-member
        sock.bind(("0.0.0.0", self.m_port))
        sock.listen(1024)
        sock.setblocking(False)

        config = uvicorn.Config(
            self.m_sio_app,
            log_level="warning",
            ssl_certfile=self.m_cert_path,
            ssl_keyfile=self.m_key_path,
        )

        self._server = uvicorn.Server(config)
        await self._server.serve(sockets=[sock])

    def register_post_start_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Register a coroutine to run after the server starts but before serving requests.

        Only one callback can be registered. A second call will overwrite the first.

        Args:
            callback (Callable[[], Awaitable[None]]): An async function to be run at startup.
        """
        self._post_start_callback = callback

    def register_on_client_connect_callback(self, callback: Callable[[ClientType, str], Awaitable[None]]) -> None:
        """
        Register a coroutine to run when a client connects.

        Args:
            callback (Callable[[ClientType, str], Awaitable[None]]): An async function to be run when a client connects.
                Should support two arguments: the client type and the session ID.
        """
        self._on_client_connect_callback = callback

    def _define_static_file_routes(self) -> None:
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
        self.m_logger.debug("Static directory: %s", assets_dir)

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
                    return await self.send_from_directory(assets_dir, file_path, mimetype=mime_type)

                _static_route.__name__ = f'serve_static_{route_path.replace("/", "_")}'
                return _static_route

            route_handler = make_static_route_handler(route, config['file'], config['mimetype'])
            self.m_app.route(route)(route_handler)

    def validate_int_get_request_param(self, param: Any, param_name: str) -> Optional[Dict[str, Any]]:
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

    async def render_template(self, template_name: str, **context: Any) -> str:
        """
        Render an HTML template with context.

        Args:
            template_name (str): Name of the template file.
            **context: Key-value pairs passed to the template.

        Returns:
            str: Rendered HTML string.
        """
        return await quart_render_template(template_name, **context)

    def jsonify(self, *args: Any, **kwargs: Any) -> Any:
        """
        Create a JSON response.

        Args:
            *args: Positional arguments to serialize.
            **kwargs: Keyword arguments to serialize.

        Returns:
            Response: A Quart JSON response.
        """
        return quart_jsonify(*args, **kwargs)

    @property
    def request(self) -> Any:
        """
        Get the current request context.

        Returns:
            Request: The current Quart request object.
        """
        return quart_request

    async def send_from_directory(self,
                                  directory: Union[str, os.PathLike],
                                  filename: str,
                                  **kwargs: Any) -> Any:
        """
        Send a file from a given directory.

        Args:
            directory (str | PathLike): The directory to serve from.
            filename (str): The name of the file to serve.
            **kwargs: Additional arguments passed to Quart's send_from_directory.

        Returns:
            Response: A Quart file response.
        """
        return await quart_send_from_directory(directory, filename, **kwargs)

    async def stop(self) -> None:
        """Stop the web server."""
        if not self._server:
            return  # Already stopped or never started

        self._server.should_exit = True
        try:
            await self._server.shutdown()
        except wsproto.utilities.LocalProtocolError:
            self.m_logger.debug("Websocket was already closing, ignoring double-close")
        finally:
            self._server = None
            self.m_logger.debug("Web server stopped")
