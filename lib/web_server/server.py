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
                 debug_mode: bool = False):
        self.m_logger: logging.Logger = logger
        self.m_port: int = port
        self.m_ver_str = ver_str
        self.m_cert_path: Optional[str] = cert_path
        self.m_key_path: Optional[str] = key_path
        self.m_debug_mode: bool = debug_mode
        if client_event_mappings:
            self.m_client_event_mappings: Dict[ClientType, List[str]] = client_event_mappings
        else:
            self.m_client_event_mappings: Dict[ClientType, List[str]] = {}
        self._post_start_callback: Optional[Callable[[], Awaitable[None]]] = None
        self._on_client_register_callback: Optional[Callable[[ClientType, str], Awaitable[None]]] = None
        self._on_client_disconnect_callback: Optional[Callable[[str], Awaitable[None]]] = None
        self.m_stats = EventCounter()

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

        @self.m_app.context_processor
        def override_url_for():
            def dated_url_for(endpoint, **values):
                if endpoint == 'static':
                    values['v'] = self.m_ver_str
                return url_for(endpoint, **values)
            return {"url_for": dated_url_for}

        @self.m_app.after_request
        async def no_html_cache(response: Response) -> Response:
            if response.content_type and response.content_type.startswith("text/html"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response

    def http_route(self, path: str, **kwargs) -> Callable:
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
                except Exception:  # pylint: disable=broad-except
                    self.m_stats.track_event("__HTTP_EXCEPTION__", route_key)
                    raise

            self.m_app.route(path, **kwargs)(wrapped)
            return func
        return decorator

    def socketio_event(self, event: str) -> Callable:
        def decorator(func: Callable[..., Coroutine]) -> Callable:
            @wraps(func)
            async def wrapped(*args: Any, **inner_kwargs: Any):
                self.m_stats.track_event("__SOCKET_IN__", "__TOTAL__")
                self.m_stats.track_event("__SOCKET_IN__", event)
                try:
                    result = await func(*args, **inner_kwargs)
                    self.m_stats.track_event("__SOCKET_IN_OK__", event)
                    return result
                except Exception:  # pylint: disable=broad-except
                    self.m_stats.track_event("__SOCKET_IN_EXCEPTION__", event)
                    raise

            self.m_sio.on(event)(wrapped)
            return func
        return decorator

    def _register_base_socketio_events(self) -> None:

        @self.m_sio.event
        async def connect(sid: str, _environ: Dict[str, Any]) -> None:
            self.m_stats.track_event("__SOCKET_IN__", "__CONNECT__")
            self.m_logger.debug("Client connected: %s", sid)

        @self.m_sio.event
        async def disconnect(sid: str) -> None:
            self.m_stats.track_event("__SOCKET_IN__", "__DISCONNECT__")
            self.m_logger.debug("Client disconnected: %s", sid)
            if self._on_client_disconnect_callback:
                await self._on_client_disconnect_callback(sid)

        @self.m_sio.on('register-client')
        async def handleClientRegistration(sid: str, data: Dict[str, str]) -> None:
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

            if client_type in {'player-stream-overlay', 'race-table', 'hud'}:
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

    async def send_to_clients_of_type(self, event: str, data: Dict[str, Any], client_type: ClientType) -> None:
        packed = msgpack.packb(data, use_bin_type=True)
        self._track_socket_emit_mcast(packed, room=str(client_type))
        await self.m_sio.emit(event, packed, room=str(client_type))

    async def send_to_clients_interested_in_event(self, event: str, data: Dict[str, Any]) -> None:
        packed = msgpack.packb(data, use_bin_type=True)
        self._track_socket_emit_mcast(packed, room=event)
        await self.m_sio.emit(event, packed, room=event)

    async def send_to_client(self, event: str, data: Dict[str, Any], client_id: str) -> None:
        packed = msgpack.packb(data, use_bin_type=True)
        self.m_stats.track_packet("__SOCKET_OUT__", "__UNICAST__", len(packed))
        await self.m_sio.emit(event, packed, to=client_id)

    def _track_socket_emit_mcast(self, payload: bytes, room: str) -> None:
        recipients = len(list(self.m_sio.manager.get_participants("/", room)))
        self.m_stats.track_packet("__SOCKET_OUT__", f"__EVENT_{room}__", len(payload) * recipients)

    def is_client_of_type_connected(self, client_type: ClientType) -> bool:
        return not self._is_room_empty(str(client_type))

    def is_any_client_interested_in_event(self, event: str) -> bool:
        return not self._is_room_empty(event)

    def _is_room_empty(self, room_name: str, namespace: Optional[str] = '/') -> bool:
        participants = list(self.m_sio.manager.get_participants(namespace, room_name))
        return not participants

    async def run(self) -> None:
        @self.m_app.before_serving
        async def before_serving() -> None:
            self.m_logger.debug("In post init ...")
            if self._post_start_callback:
                await self._post_start_callback()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if platform.system() != "Windows":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(("0.0.0.0", self.m_port))
        except OSError as e:
            sock.close()
            if is_port_in_use_error(e.errno):
                self.m_logger.error("Port %s is already in use", self.m_port)
                raise PngHttpPortInUseError() from e
            raise

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
        self._post_start_callback = callback

    def register_on_client_register_callback(self, callback: Callable[[ClientType, str], Awaitable[None]]) -> None:
        self._on_client_register_callback = callback

    def register_on_client_disconnect_callback(self, callback: Callable[[str], Awaitable[None]]) -> None:
        self._on_client_disconnect_callback = callback

    def _define_static_file_routes(self) -> None:
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

        assets_dir = self.m_base_dir / "assets"
        self.m_logger.debug("Static directory: %s", assets_dir)

        for route, config in static_routes.items():
            def make_static_route_handler(route_path: str, file_path: str, mime_type: str):
                async def _static_route():
                    return await self.send_from_directory(assets_dir, file_path, mimetype=mime_type)

                _static_route.__name__ = f'serve_static_{route_path.replace("/", "_")}'
                return _static_route

            route_handler = make_static_route_handler(route, config['file'], config['mimetype'])
            self.m_app.route(route)(route_handler)

    def validate_int_get_request_param(self, param: Any, param_name: str) -> Optional[Dict[str, Any]]:
        if param is None:
            return {
                'error': 'Invalid parameters',
                'message': f'Provide "{param_name}" parameter'
            }

        if not isinstance(param, int) and not str(param).isdigit():
            return {
                'error': 'Invalid parameter value',
                'message': f'"{param_name}" parameter must be numeric'
            }

        return None

    async def render_template(self, template_name: str, **context: Any) -> str:
        return await quart_render_template(template_name, **context)

    def jsonify(self, *args: Any, **kwargs: Any) -> Any:
        return quart_jsonify(*args, **kwargs)

    @property
    def request(self) -> Any:
        return quart_request

    async def send_from_directory(self,
                                  directory: Union[str, os.PathLike],
                                  filename: str,
                                  **kwargs: Any) -> Any:
        self.m_stats.track_event("__STATIC__", filename)
        return await quart_send_from_directory(directory, filename, **kwargs)

    def get_stats(self) -> dict:
        return self.m_stats.get_stats()

    async def stop(self) -> None:
        if not self._server:
            return

        self._server.should_exit = True
        try:
            await self._server.shutdown()
        except wsproto.utilities.LocalProtocolError:
            self.m_logger.debug("Websocket was already closing, ignoring double-close")
        finally:
            self._server = None
            self.m_logger.debug("Web server stopped")
