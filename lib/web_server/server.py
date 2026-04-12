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

import logging
import os
import platform
import socket
from functools import wraps
from pathlib import Path
from typing import (Any, Awaitable, Callable, Coroutine, Dict, List, Optional,
                    Union)

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

from lib.error_status import PngHttpPortInUseError, is_port_in_use_error
from lib.event_counter import EventCounter

from .client_types import ClientType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseWebServer:
    """Base class for a web server. Derived classes must implement their routes of interest"""
    def __init__(self,
                 port: int,
                 ver_str: str,
                 logger: logging.Logger,
                 client_event_mappings: Dict[ClientType, List[str]] = None,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None,
                 debug_mode: bool = False,
                 additional_ports: Optional[List[Dict[str, Any]]] = None,
                 bind_address: str = "0.0.0.0"):
        """
        Initialize the BaseWebServer.

        Args:
            port (int): The port number to run the server on.
            ver_str (str): The version string.
            logger (logging.Logger): The logger instance.
            client_event_mappings (Dict[ClientType, str], optional): A dictionary mapping client types to event names.
            cert_path (Optional[str], optional): Path to the certificate file. Defaults to None.
            key_path (Optional[str], optional): Path to the key file. Defaults to None.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
            additional_ports (Optional[List[Dict[str, Any]]], optional): Additional ports with labels for multi-session.
        """
        self.m_logger: logging.Logger = logger
        self.m_port: int = port
        self.m_ver_str = ver_str
        self.m_cert_path: Optional[str] = cert_path
        self.m_key_path: Optional[str] = key_path
        self.m_debug_mode: bool = debug_mode
        self.m_bind_address: str = bind_address
        if client_event_mappings:
            self.m_client_event_mappings: Dict[ClientType, List[str]] = client_event_mappings
        else:
            self.m_client_event_mappings: Dict[ClientType, List[str]] = {}
        self._post_start_callback: Optional[Callable[[], Awaitable[None]]] = None
        self._on_client_register_callback: Optional[Callable[[ClientType, str], Awaitable[None]]] = None
        self._on_client_disconnect_callback: Optional[Callable[[str], Awaitable[None]]] = None
        self.m_stats = EventCounter()

        # Multi-port: build port → label mapping
        self.m_additional_ports: List[Dict[str, Any]] = additional_ports or []
        self.m_port_labels: Dict[int, str] = {}
        for entry in self.m_additional_ports:
            self.m_port_labels[entry["port"]] = entry.get("label", "")
        self.m_is_multi_port: bool = len(self.m_additional_ports) > 0

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
            cors_allowed_origins=self._compute_cors_origins(),
            logger=False,
            engineio_logger=False
        )
        self.m_sio_app: socketio.ASGIApp = socketio.ASGIApp(self.m_sio, self.m_app)
        self._server: Optional[uvicorn.Server] = None

        self._register_base_socketio_events()
        self._define_static_file_routes()
        self._sid_port_map: Dict[str, int] = {}  # sid → port the client connected on

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

        # Inject port_info template variable for multi-port badge
        @self.m_app.context_processor
        def inject_port_info():
            if not self.m_is_multi_port:
                return {"port_info": None, "port_label": "", "port_number": self.m_port}
            # Determine which port this request arrived on via ASGI scope
            try:
                server_tuple = quart_request.scope.get("server", (None, None))
                req_port = server_tuple[1] if server_tuple else self.m_port
            except RuntimeError:
                req_port = self.m_port
            label = self.m_port_labels.get(req_port, "(Primary)" if req_port == self.m_port else "")
            port_info = f":{req_port} {label}".strip() if label else f":{req_port}"
            return {"port_info": port_info, "port_label": label, "port_number": req_port}

        # Disable caching for template paths, always.
        @self.m_app.after_request
        async def no_html_cache(response: Response) -> Response:
            # Only apply to HTML responses
            if response.content_type and response.content_type.startswith("text/html"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

            # Security headers (C-003)
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            if self.m_cert_path:
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            return response

    def http_route(self, path: str, **kwargs) -> Callable:
        """Register a HTTP route."""
        def decorator(func: Callable[..., Coroutine]) -> Callable:
            @wraps(func)
            async def wrapped(*args: Any, **inner_kwargs: Any):
                method = quart_request.method if quart_request else "UNKNOWN"
                route_key = f"{method} {path}"
                self.m_stats.track_event("__HTTP__", "__TOTAL__")
                self.m_stats.track_event("__HTTP__", route_key)
                try:
                    result = await func(*args, **inner_kwargs)
                    self.m_stats.track_event("__HTTP_OK__", route_key)
                    return result
                except Exception:  # pylint: disable=broad-exception-caught
                    self.m_stats.track_event("__HTTP_EXCEPTION__", route_key)
                    raise

            self.m_app.route(path, **kwargs)(wrapped)
            return func
        return decorator

    def socketio_event(self, event: str) -> Callable:
        """Register a SocketIO event."""
        def decorator(func: Callable[..., Coroutine]) -> Callable:
            @wraps(func)
            async def wrapped(*args: Any, **inner_kwargs: Any):
                self.m_stats.track_event("__SOCKET_IN__", "__TOTAL__")
                self.m_stats.track_event("__SOCKET_IN__", event)
                try:
                    result = await func(*args, **inner_kwargs)
                    self.m_stats.track_event("__SOCKET_IN_OK__", event)
                    return result
                except Exception:  # pylint: disable=broad-exception-caught
                    self.m_stats.track_event("__SOCKET_IN_EXCEPTION__", event)
                    raise

            self.m_sio.on(event)(wrapped)
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
            self.m_stats.track_event("__SOCKET_IN__", "__CONNECT__")
            self.m_logger.debug("Client connected: %s", sid)
            # Extract the port from the ASGI scope and store for later use
            port = _environ.get('asgi.scope', {}).get('server', (None, None))[1]
            if port is not None:
                self._sid_port_map[sid] = port

        @self.m_sio.event
        async def disconnect(sid: str) -> None:
            """
            Handle client disconnection event.

            Args:
                sid (str): Session ID of the disconnected client.
            """
            self.m_stats.track_event("__SOCKET_IN__", "__DISCONNECT__")
            self.m_logger.debug("Client disconnected: %s", sid)
            self._sid_port_map.pop(sid, None)
            if self._on_client_disconnect_callback:
                await self._on_client_disconnect_callback(sid)

        @self.m_sio.on('register-client')
        async def handleClientRegistration(sid: str, data: Dict[str, str]) -> None:
            """
            Handle client registration for specific client types. Add client to room named after client type.
            Also add client to room named after events it is interested in (if client event mappings are defined).

            Args:
                sid (str): Session ID of the registering client.
                data (Dict[str, str]): Registration data containing client type.
            """
            client_type = data.get('type')
            self.m_stats.track_event("__SOCKET_IN__", "register-client")
            self.m_logger.debug('[CLIENT_REG] Client registered. SID = %s Type = %s ID=%s',
                                sid, client_type, data.get('id', 'N/A'))
            if not client_type:
                self.m_stats.track_event("__SOCKET_IN_INVALID__", "missing-client-type")
                return

            try:
                parsed_client_type = ClientType(client_type)
            except ValueError:
                self.m_stats.track_event("__SOCKET_IN_INVALID__", "unknown-client-type")
                return

            if client_type in {ct.value for ct in ClientType}:
                self.m_stats.track_event("__CLIENT_REG__", client_type)
                await self.m_sio.enter_room(sid, client_type)
                if self._on_client_register_callback:
                    await self._on_client_register_callback(parsed_client_type, sid)
                if self.m_debug_mode:
                    self.m_logger.debug('[CLIENT_REG] Client %s joined room %s', sid, client_type)

                    room = self.m_sio.manager.rooms.get('/', {}).get(client_type)
                    self.m_logger.debug('[CLIENT_REG] Current members of %s: %s', client_type, room)

            interested_events = self.m_client_event_mappings.get(parsed_client_type)
            if interested_events:
                for event in interested_events:
                    await self.m_sio.enter_room(sid, event)
                    if self.m_debug_mode:
                        self.m_logger.debug('Client %s joined room %s', sid, event)

                        room = self.m_sio.manager.rooms.get('/', {}).get(event)
                        self.m_logger.debug('[CLIENT_REG] Current members of %s: %s', event, room)

            # Port-specific rooms (additive — client stays in global rooms too)
            conn_port = self._sid_port_map.get(sid)
            if conn_port is not None and interested_events:
                for event in interested_events:
                    port_room = f"port:{conn_port}:{event}"
                    await self.m_sio.enter_room(sid, port_room)
                    if self.m_debug_mode:
                        self.m_logger.debug('[CLIENT_REG] Client %s joined port room %s', sid, port_room)

    async def send_to_clients_of_type(self, event: str, data: Dict[str, Any], client_type: ClientType) -> None:
        """
        Send data to clients in a specific room.

        Args:
            event (str): The event name to send.
            data (Dict[str, Any]): The data to send with the event.
            client_type (ClientType): The client type to send the event to.
        """
        packed = msgpack.packb(data, use_bin_type=True)
        self._track_socket_emit_mcast(packed, room=str(client_type))
        await self.m_sio.emit(event, packed, room=str(client_type))

    async def send_to_clients_interested_in_event(self, event: str, data: Dict[str, Any]) -> None:
        """
        Send data to all clients interested in a particular event, based on given client_event_mappings.

        Args:
            event (str): The event name to send.
            data (Dict[str, Any]): The data to send with the event.
        """
        packed = msgpack.packb(data, use_bin_type=True)
        self._track_socket_emit_mcast(packed, room=event)
        await self.m_sio.emit(event, packed, room=event)

    async def send_to_client(self, event: str, data: Dict[str, Any], client_id: str) -> None:
        """
        Send data to clients in a specific room.

        Args:
            event (str): The event name to send.
            data (Dict[str, Any]): The data to send with the event.
            client_id (str): The client ID to send the event to.
        """
        packed = msgpack.packb(data, use_bin_type=True)
        self.m_stats.track_packet("__SOCKET_OUT__", "__UNICAST__", len(packed))
        await self.m_sio.emit(event, packed, to=client_id)

    def _track_socket_emit_mcast(self,
                           payload: bytes,
                           room: str) -> None:
        """Track outbound socket payload fan-out bytes/counter."""
        recipients = len(list(self.m_sio.manager.get_participants("/", room)))

        # Account for each recipient separately so packet count reflects actual fan-out.
        self.m_stats.track_packet("__SOCKET_OUT__", f"__EVENT_{room}__", len(payload) * recipients)

    def is_client_of_type_connected(self, client_type: ClientType) -> bool:
        """Check if a client of a specific type is connected

        Args:
            client_type (ClientType): The client type to check

        Returns:
            bool: True if a client of the specified type is connected
        """
        return not self._is_room_empty(str(client_type))

    def is_any_client_interested_in_event(self, event: str) -> bool:
        """Check if any client is interested in an event

        Args:
            event (str): The event to check

        Returns:
            bool: True if any client is interested in the event
        """
        return not self._is_room_empty(event)

    async def send_to_port_room(self, port: int, event: str, data: Dict[str, Any]) -> None:
        """Send data only to clients connected on a specific port that are interested in an event.

        Args:
            port (int): The port the clients connected on.
            event (str): The event name to emit.
            data (Dict[str, Any]): The data to send with the event.
        """
        port_room = f"port:{port}:{event}"
        packed = msgpack.packb(data, use_bin_type=True)
        await self.m_sio.emit(event, packed, room=port_room)

    def is_any_client_in_port_room(self, port: int, event: str) -> bool:
        """Check if any client is in a port-specific room.

        Args:
            port (int): The port to check.
            event (str): The event name to check.

        Returns:
            bool: True if any client is in the port-specific room.
        """
        port_room = f"port:{port}:{event}"
        return not self._is_room_empty(port_room)

    def _is_room_empty(self, room_name: str, namespace: Optional[str] = '/') -> bool:
        """Check if a room is empty"""
        participants = list(self.m_sio.manager.get_participants(namespace, room_name))
        return not participants

    async def run(self) -> None:
        """
        Run the web server asynchronously using Uvicorn.

        Sets up the server configuration and starts serving the application.
        When additional_ports are configured, binds multiple sockets so the
        same ASGI app is served on all ports.

        Raises:
            PngHttpPortInUseError: If the primary port is already in use.
            OSError: If the server fails to start and error is not a port in use error.
        """
        # Register post start callback before running
        @self.m_app.before_serving
        async def before_serving() -> None:
            self.m_logger.debug("In post init ...")
            if self._post_start_callback:
                await self._post_start_callback()

        sockets: List[socket.socket] = []

        # --- Primary port (mandatory — failure is fatal) ---
        primary_sock = self._create_socket(self.m_port)
        if primary_sock is None:
            raise PngHttpPortInUseError()
        sockets.append(primary_sock)

        # --- Additional ports (optional — failure is a warning) ---
        for entry in self.m_additional_ports:
            extra_port = entry["port"]
            extra_label = entry.get("label", "")
            extra_sock = self._create_socket(extra_port)
            if extra_sock is None:
                label_str = f" '{extra_label}'" if extra_label else ""
                self.m_logger.warning(
                    "Multi-session port %d%s could not be bound — skipping",
                    extra_port, label_str
                )
                continue
            sockets.append(extra_sock)

        config = uvicorn.Config(
            self.m_sio_app,
            log_level="warning",
            ssl_certfile=self.m_cert_path,
            ssl_keyfile=self.m_key_path,
        )

        self._server = uvicorn.Server(config)
        await self._server.serve(sockets=sockets)

    def _create_socket(self, port: int) -> Optional[socket.socket]:
        """Create and bind a TCP socket on the given port.

        Returns the socket on success, or None if the port is in use.
        Raises OSError for non-port-in-use errors.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if platform.system() != "Windows":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind((self.m_bind_address, port))
        except OSError as e:
            sock.close()
            if is_port_in_use_error(e.errno):
                self.m_logger.error("Port %d is already in use", port)
                return None
            raise

        sock.listen(1024)
        sock.setblocking(False)
        return sock

    def _compute_cors_origins(self) -> Union[str, List[str]]:
        """Compute CORS allowed origins based on the bind address.

        When bound to localhost/127.0.0.1, restrict origins to localhost URLs.
        When bound to 0.0.0.0 or other addresses (LAN mode), allow all origins
        because clients connect from various IPs on the network.
        """
        local_addresses = ("127.0.0.1", "localhost")
        if self.m_bind_address in local_addresses:
            scheme = "https" if self.m_cert_path else "http"
            origins = [
                f"{scheme}://localhost:{self.m_port}",
                f"{scheme}://127.0.0.1:{self.m_port}",
            ]
            for entry in self.m_additional_ports:
                origins.append(f"{scheme}://localhost:{entry['port']}")
                origins.append(f"{scheme}://127.0.0.1:{entry['port']}")
            return origins
        return "*"

    def register_post_start_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        Register a coroutine to run after the server starts but before serving requests.

        Only one callback can be registered. A second call will overwrite the first.

        Args:
            callback (Callable[[], Awaitable[None]]): An async function to be run at startup.
        """
        self._post_start_callback = callback

    def register_on_client_register_callback(self, callback: Callable[[ClientType, str], Awaitable[None]]) -> None:
        """
        Register a coroutine to run when a client registers.

        Args:
            callback (Callable[[ClientType, str], Awaitable[None]]): An async function to be run when a client registers
                Should support two arguments: the client type and the session ID.
        """
        self._on_client_register_callback = callback

    def register_on_client_disconnect_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """
        Register a coroutine to run when a client disconnects.

        Args:
            callback (Callable[[str], Awaitable[None]]): An async function to be run when a client disconnects
                Should support 1 arguments: the session ID.
        """
        self._on_client_disconnect_callback = callback

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

        # Dynamic routes for track map SVGs and transforms, organized by game year.
        # send_from_directory handles path-traversal protection via safe_join.
        track_maps_dir = assets_dir / "track-maps"

        # Per-game SVG transforms: /track-maps/f1_2025/svg_transforms.json
        async def serve_svg_transforms(game_year: str):
            game_dir = track_maps_dir / f"f1_{game_year}"
            return await self.send_from_directory(game_dir, 'svg_transforms.json',
                                                  mimetype='application/json')

        self.m_app.route('/track-maps/f1_<game_year>/svg_transforms.json')(serve_svg_transforms)

        # Per-game SVG track maps: /track-maps/f1_2025/Singapore.svg
        async def serve_track_map(game_year: str, filename: str):
            game_dir = track_maps_dir / f"f1_{game_year}"
            return await self.send_from_directory(game_dir, filename, mimetype='image/svg+xml')

        self.m_app.route('/track-maps/f1_<game_year>/<filename>')(serve_track_map)

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
        self.m_stats.track_event("__STATIC__", filename)
        return await quart_send_from_directory(directory, filename, **kwargs)

    def get_stats(self) -> dict:
        """Get current web server stats snapshot."""
        return self.m_stats.get_stats()

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
