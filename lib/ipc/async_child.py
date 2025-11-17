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

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcChildAsync:
    """
    Asynchronous ZeroMQ REP socket server.
    Used by child process to handle requests using asyncio.
    Can be run as a background asyncio task.
    Includes optional heartbeat monitoring.
    """

    def __init__(self, port: int, name: str = "IpcChildAsync", max_missed_heartbeats: int = 3,
                 heartbeat_timeout: float = 5.0):
        """
        :param port: Port to bind to.
        :param name: Name for logging purposes.
        :param max_missed_heartbeats: Number of consecutive missed heartbeats before calling callback.
        :param heartbeat_timeout: Time in seconds to wait for heartbeat before considering it missed.
        """
        self.name = name
        self.endpoint = f"tcp://127.0.0.1:{port}"
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.REP)
        self.sock.bind(self.endpoint)
        self._running = False
        self._shutdown_callback = None

        # Heartbeat monitoring (only active if callback is registered)
        self.max_missed_heartbeats = max_missed_heartbeats
        self.heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat = None
        self._missed_heartbeats = 0
        self._heartbeat_missed_callback = self._def_heartbeat_missed_callback
        self._heartbeat_task = None

    def register_shutdown_callback(self, callback: Callable[[dict], Awaitable[dict]]):
        """
        Registers an async callback to be called before shutdown.
        Callback must return a dict with 'status' and 'message' keys.
        """
        self._shutdown_callback = callback

    def register_heartbeat_missed_callback(self, callback: Callable[[int], Awaitable[None]]):
        """
        Registers an async callback to be called when max consecutive heartbeats are missed.
        Callback receives the number of missed heartbeats.
        Registering this callback automatically enables heartbeat monitoring.
        """
        self._heartbeat_missed_callback = callback

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
                print(f"[{self.name}] Error in heartbeat monitor: {e}")
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

                # Check if we've missed too many consecutive heartbeats
                if self._missed_heartbeats >= self.max_missed_heartbeats:
                    try:
                        await self._heartbeat_missed_callback(self._missed_heartbeats)
                        break
                    except Exception as e: # pylint: disable=broad-exception-caught
                        print(f"[{self.name}] Error in heartbeat missed callback: {e}")

    def _handle_heartbeat(self) -> dict:
        """
        Handles incoming heartbeat and resets missed counter.
        """
        self._last_heartbeat = time.time()
        self._missed_heartbeats = 0
        return {"status": "success", "reply": "__heartbeat_ack__", "source": self.name}

    async def run(self, handler_fn: Callable[[dict], Awaitable[dict]], timeout: Optional[int] = None) -> None:
        """
        Starts the async request loop. Calls await handler_fn(msg) on each request.
        Stops if a 'quit' command is received.
        :param handler_fn: Coroutine function to handle commands
        :param timeout: Optional timeout for recv in seconds
        """
        self._running = True

        # Start heartbeat monitoring only if callback is registered
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
                    print(f"[{self.name}] Timeout waiting for request")
                    continue  # go back and recv again

                cmd = msg.get("cmd")

                # 2) dispatch + error handling
                try:
                    if cmd == "__terminate__":
                        break

                    if cmd == "__heartbeat__":
                        response = self._handle_heartbeat()

                    elif cmd == "__ping__":
                        response = {"reply": "__pong__", "source": self.name}

                    elif cmd == "__shutdown__":
                        if self._shutdown_callback:
                            response = await self._shutdown_callback(msg.get("args", {}))
                        else:
                            response = {
                                "status": "success",
                                "message": "default shutdown complete",
                            }
                        self._running = False

                    else:
                        response = await handler_fn(msg)

                except Exception as e: # pylint: disable=broad-except
                    response = {"error": str(e)}

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

    async def _def_heartbeat_missed_callback(self, _missed_heartbeats: int) -> Awaitable[None]:
        """Default heartbeat missed callback. Hard kills the app"""
        return

    def close(self) -> None:
        """Closes the socket."""
        self._running = False
        self.sock.close()
        self.ctx.term()
