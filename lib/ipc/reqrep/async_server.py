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
import time
from typing import Awaitable, Callable, Optional

import zmq
import zmq.asyncio
import logging

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcServerAsync:
    """
    Asynchronous ZeroMQ REP socket server.
    Used by child process to handle requests using asyncio.
    Can be run as a background asyncio task.
    Includes optional heartbeat monitoring.
    """

    BUILTIN_COMMANDS = {"__terminate__", "__heartbeat__", "__shutdown__", "__ping__"}

    def __init__(self, port: int | None = None, name: str = "IpcChildAsync",
             max_missed_heartbeats: int = 3, heartbeat_timeout: float = 5.0,
             logger: Optional[logging.Logger] = None):
        """
        :param port: Port to bind to.
        :param name: Name for logging purposes.
        :param max_missed_heartbeats: Number of consecutive missed heartbeats before calling callback.
        :param heartbeat_timeout: Time in seconds to wait for heartbeat before considering it missed.
        :param logger: Logger to use.
        """
        self.name = name
        self.endpoint = f"tcp://127.0.0.1:{port}"
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.REP)

        # ------------------------------------------------------------------
        # 1. Bind to OS-assigned port when port is None
        # ------------------------------------------------------------------
        if port is None:
            self.sock.bind("tcp://127.0.0.1:*")
            endpoint = self.sock.getsockopt(zmq.LAST_ENDPOINT).decode()
            # endpoint looks like: "tcp://127.0.0.1:52431"
            self.endpoint = endpoint
            self.port = int(endpoint.rsplit(":", 1)[1])
        else:
            self.endpoint = f"tcp://127.0.0.1:{port}"
            self.port = port
            self.sock.bind(self.endpoint)

        self._running = False
        self._shutdown_callback: Optional[Callable[[dict], Awaitable[dict]]] = None
        self._command_handlers: dict[str, Callable[[dict], Awaitable[dict]]] = {}
        self._register_builtin_handlers()

        # Heartbeat monitoring (only active if callback is registered)
        self.max_missed_heartbeats = max_missed_heartbeats
        self.heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat = None
        self._missed_heartbeats = 0
        self._heartbeat_missed_callback: Optional[Callable[[int], Awaitable[None] | None]] = None
        self._heartbeat_task = None

        if logger is None:
            logger = logging.getLogger(f"{__name__}")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

    def _register_builtin_handlers(self) -> None:
        """Registers builtin command handlers."""
        self._command_handlers["__terminate__"] = self._handle_terminate
        self._command_handlers["__heartbeat__"] = self._handle_heartbeat
        self._command_handlers["__shutdown__"] = self._handle_shutdown
        self._command_handlers["__ping__"] = self._handle_ping

    def on_command(self, cmd_name: str) -> Callable[[Callable[[dict], Awaitable[dict]]], Callable[[dict], Awaitable[dict]]]:
        """Registers a handler for a non-builtin command using decorator syntax."""
        if cmd_name in self.BUILTIN_COMMANDS:
            raise ValueError(f"'{cmd_name}' is a reserved builtin command")

        def decorator(callback: Callable[[dict], Awaitable[dict]]) -> Callable[[dict], Awaitable[dict]]:
            self._command_handlers[cmd_name] = callback
            return callback

        return decorator

    def on_shutdown(self, callback: Callable[[dict], Awaitable[dict]]) -> Callable[[dict], Awaitable[dict]]:
        """Registers a shutdown callback using decorator syntax."""
        self._shutdown_callback = callback
        return callback

    def on_heartbeats_missed(self, callback: Callable[[int], Awaitable[None] | None]) -> Callable[[int], Awaitable[None] | None]:
        """Registers a heartbeat-missed callback using decorator syntax."""
        self._heartbeat_missed_callback = callback
        return callback

    @property
    def is_running(self) -> bool:
        return self._running

    async def _heartbeat_monitor(self) -> None:
        """
        Background task that monitors heartbeats.
        Only runs if a heartbeat callback is registered.
        """
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_timeout)
            except asyncio.CancelledError:
                break
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.exception("%s: Error in heartbeat monitor. %s", self.name, e)
                break

            if not self._running:
                break

            # Check if we've received our first heartbeat
            if self._last_heartbeat is None:
                continue

            # Check if heartbeat is overdue
            current_time = time.time()
            time_since_last = current_time - self._last_heartbeat
            if time_since_last > self.heartbeat_timeout:
                self._missed_heartbeats += 1
                self.logger.debug("%s: Missed heartbeat. count: %d", self.name, self._missed_heartbeats)

                # Check if we've missed too many consecutive heartbeats
                if self._missed_heartbeats >= self.max_missed_heartbeats:
                    try:
                        callback = self._heartbeat_missed_callback or self._def_heartbeat_missed_callback
                        result = callback(self._missed_heartbeats)
                        if asyncio.iscoroutine(result):
                            await result
                        break
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self.logger.exception("%s: Error in heartbeat missed callback. %s", self.name, e)

    async def _handle_terminate(self, _args: dict) -> dict:
        """Handles force termination."""
        self._running = False
        return {"status": "success", "message": "terminated", "source": self.name}

    async def _handle_heartbeat(self, _args: dict) -> dict:
        """
        Handles incoming heartbeat and resets missed counter.
        """
        self._last_heartbeat = time.time()
        self._missed_heartbeats = 0
        return {"status": "success", "reply": "__heartbeat_ack__", "source": self.name}

    async def _handle_shutdown(self, args: dict) -> dict:
        """Handles graceful shutdown."""
        if self._shutdown_callback:
            response = await self._shutdown_callback(args)
        else:
            response = {
                "status": "success",
                "message": "default shutdown complete",
            }
        self._running = False
        return response

    async def _handle_ping(self, _args: dict) -> dict:
        """Handles ping command."""
        return {"reply": "__pong__", "source": self.name}

    async def _dispatch_command(self, msg: dict) -> dict:
        """Routes a command to builtin handlers or user-registered handlers."""
        cmd = msg.get("cmd")
        args = msg.get("args", {})

        handler = self._command_handlers.get(cmd)
        if handler is None:
            return {"status": "error", "message": f"unknown command: {cmd}", "source": self.name}

        return await handler(args)

    async def run(self, timeout: Optional[int] = None) -> None:
        """
        Starts the async request loop and routes commands to registered handlers.
        :param timeout: Optional timeout for recv in seconds
        """
        self._running = True

        # Start heartbeat monitoring only if callback is registered
        if self._heartbeat_missed_callback is not None:
            self._last_heartbeat = time.time()
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

        try:
            while self._running:
                # 1) receive with optional timeout
                try:
                    if timeout:
                        msg = await asyncio.wait_for(self.sock.recv_json(), timeout)
                    else:
                        msg = await self.sock.recv_json()
                except asyncio.TimeoutError:
                    self.logger.warning("%s: Timeout waiting for request", self.name)
                    continue  # go back and recv again

                # 2) dispatch + error handling
                try:
                    response = await self._dispatch_command(msg)

                except Exception as e: # pylint: disable=broad-except
                    response = {
                        "status" : "error",
                        "message": str(e)
                    }

                # 3) always send back one JSON
                await self.sock.send_json(response)

        finally:
            # Clean up heartbeat monitoring
            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass

            self.close()
            self._running = False

    async def _def_heartbeat_missed_callback(self, _missed_heartbeats: int) -> None:
        """Default heartbeat missed callback. no-op"""
        return

    def close(self) -> None:
        """Closes the socket."""
        self.logger.debug("%s closing", self.name)
        self._running = False
        self.sock.close()
        self.ctx.term()
