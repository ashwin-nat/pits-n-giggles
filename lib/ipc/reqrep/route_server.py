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

import asyncio
import inspect
import threading
from typing import Any, Awaitable, Callable, Optional

from .async_server import IpcServerAsync
from .sync_server import IpcServerSync

# -------------------------------------- TYPES -------------------------------------------------------------------------

RouteCallback = Callable[[dict], dict[str, Any] | Awaitable[dict[str, Any]]]
ShutdownCallback = Callable[[dict], dict[str, Any] | Awaitable[dict[str, Any]]]
HeartbeatCallback = Callable[[int], None | Awaitable[None]]

# -------------------------------------- HELPERS -----------------------------------------------------------------------

async def _resolve_async_result(result: Any) -> Any:
    """Resolve result that can be either direct value or awaitable."""
    if inspect.isawaitable(result):
        return await result
    return result

def _resolve_sync_result(result: Any) -> Any:
    """Resolve result in sync mode; can run awaitables if no loop is active."""
    if not inspect.isawaitable(result):
        return result

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        async def _await_result():
            return await result

        return asyncio.run(_await_result())

    raise RuntimeError(
        "Received an awaitable callback result in sync mode while an event loop is already running."
    )

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcServerAsyncRouter:
    """
    Decorator-based async wrapper around IpcServerAsync.
    """

    def __init__(self, **server_kwargs):
        self._server = IpcServerAsync(**server_kwargs)
        self._route_handlers: dict[str, RouteCallback] = {}
        self._shutdown_handler: Optional[ShutdownCallback] = None
        self._heartbeat_missed_handler: Optional[HeartbeatCallback] = None

    # -------------------------------------- DECORATORS ----------------------------------------------------------------

    def on(self, cmd_name: str) -> Callable[[RouteCallback], RouteCallback]:
        if not cmd_name:
            raise ValueError("cmd_name cannot be empty")

        def decorator(func: RouteCallback) -> RouteCallback:
            self._route_handlers[cmd_name] = func
            return func

        return decorator

    def on_shutdown(self, func: ShutdownCallback) -> ShutdownCallback:
        self._shutdown_handler = func
        self._server.register_shutdown_callback(self._dispatch_shutdown)
        return func

    def on_heartbeat_missed(self, func: HeartbeatCallback) -> HeartbeatCallback:
        self._heartbeat_missed_handler = func
        self._server.register_heartbeat_missed_callback(self._dispatch_heartbeat_missed)
        return func

    # -------------------------------------- MAIN RUNNER ---------------------------------------------------------------

    async def run(self, timeout: Optional[int] = None) -> None:
        await self._server.run(self._dispatch_request, timeout=timeout)

    # -------------------------------------- PUBLIC API ----------------------------------------------------------------

    @property
    def port(self) -> int:
        return self._server.port

    @property
    def endpoint(self) -> str:
        return self._server.endpoint

    @property
    def name(self) -> str:
        return self._server.name

    @property
    def is_running(self) -> bool:
        return self._server.is_running

    def close(self) -> None:
        self._server.close()

    # -------------------------------------- DISPATCHERS ---------------------------------------------------------------

    async def _dispatch_request(self, msg: dict) -> dict[str, Any]:
        cmd = msg.get("cmd")
        if not cmd:
            return {"status": "error", "message": "Missing command name"}

        handler = self._route_handlers.get(cmd)
        if not handler:
            return {"status": "error", "message": f"Unknown command: {cmd}"}

        result = handler(msg)
        return await _resolve_async_result(result)

    async def _dispatch_shutdown(self, args: dict) -> dict[str, Any]:
        if not self._shutdown_handler:
            return {
                "status": "success",
                "message": "default shutdown complete",
            }
        result = self._shutdown_handler(args)
        return await _resolve_async_result(result)

    async def _dispatch_heartbeat_missed(self, count: int) -> None:
        if not self._heartbeat_missed_handler:
            return
        result = self._heartbeat_missed_handler(count)
        await _resolve_async_result(result)

class IpcServerSyncRouter:
    """
    Decorator-based sync wrapper around IpcServerSync.
    """

    def __init__(self, **server_kwargs):
        self._server = IpcServerSync(**server_kwargs)
        self._route_handlers: dict[str, RouteCallback] = {}
        self._shutdown_handler: Optional[ShutdownCallback] = None
        self._heartbeat_missed_handler: Optional[HeartbeatCallback] = None

    # -------------------------------------- DECORATORS ----------------------------------------------------------------

    def on(self, cmd_name: str) -> Callable[[RouteCallback], RouteCallback]:
        if not cmd_name:
            raise ValueError("cmd_name cannot be empty")

        def decorator(func: RouteCallback) -> RouteCallback:
            self._route_handlers[cmd_name] = func
            return func

        return decorator

    def on_shutdown(self, func: ShutdownCallback) -> ShutdownCallback:
        self._shutdown_handler = func
        self._server.register_shutdown_callback(self._dispatch_shutdown)
        return func

    def on_heartbeat_missed(self, func: HeartbeatCallback) -> HeartbeatCallback:
        self._heartbeat_missed_handler = func
        self._server.register_heartbeat_missed_callback(self._dispatch_heartbeat_missed)
        return func

    # -------------------------------------- MAIN RUNNERS --------------------------------------------------------------

    def serve(self, timeout: Optional[float] = None) -> None:
        self._server.serve(self._dispatch_request, timeout=timeout)

    def serve_in_thread(self, timeout: Optional[float] = None, name: Optional[str] = None) -> threading.Thread:
        return self._server.serve_in_thread(self._dispatch_request, timeout=timeout, name=name)

    # -------------------------------------- PUBLIC API ----------------------------------------------------------------

    @property
    def port(self) -> int:
        return self._server.port

    @property
    def endpoint(self) -> str:
        return self._server.endpoint

    @property
    def name(self) -> str:
        return self._server.name

    @property
    def is_running(self) -> bool:
        return self._server.is_running

    def close(self) -> None:
        self._server.close()

    # -------------------------------------- DISPATCHERS ---------------------------------------------------------------

    def _dispatch_request(self, msg: dict) -> dict[str, Any]:
        cmd = msg.get("cmd")
        if not cmd:
            return {"status": "error", "message": "Missing command name"}

        handler = self._route_handlers.get(cmd)
        if not handler:
            return {"status": "error", "message": f"Unknown command: {cmd}"}

        result = handler(msg)
        return _resolve_sync_result(result)

    def _dispatch_shutdown(self, args: dict) -> dict[str, Any]:
        if not self._shutdown_handler:
            return {
                "status": "success",
                "message": "default shutdown complete",
            }
        result = self._shutdown_handler(args)
        return _resolve_sync_result(result)

    def _dispatch_heartbeat_missed(self, count: int) -> None:
        if not self._heartbeat_missed_handler:
            return
        result = self._heartbeat_missed_handler(count)
        _resolve_sync_result(result)
