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
from typing import Awaitable, Callable, Optional

import zmq
import zmq.asyncio

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcChildAsync:
    """
    Asynchronous ZeroMQ REP socket server.
    Used by child process to handle requests using asyncio.
    Can be run as a background asyncio task.
    """

    def __init__(self, port: int, name: str = "IpcChildAsync"):
        """
        :param port: Port to bind to.
        """
        self.name = name
        self.endpoint = f"tcp://127.0.0.1:{port}"
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.REP)
        self.sock.bind(self.endpoint)
        self._running = False
        self._shutdown_callback = None  # NEW

    def register_shutdown_callback(self, callback: Callable[[dict], Awaitable[dict]]):
        """
        Registers an async callback to be called before shutdown.
        Callback must return a dict with 'status' and 'message' keys.
        """
        self._shutdown_callback = callback

    async def run(self, handler_fn: Callable[[dict], Awaitable[dict]], timeout: Optional[int] = None) -> None:
        """
        Starts the async request loop. Calls await handler_fn(msg) on each request.
        Stops if a 'quit' command is received.
        :param handler_fn: Coroutine function to handle commands
        :param timeout: Optional timeout for recv in seconds
        """
        self._running = True

        while self._running:
            # 1) receive with optional timeout
            try:
                if timeout:
                    msg = await asyncio.wait_for(self.sock.recv_json(), timeout)
                else:
                    msg = await self.sock.recv_json()
            except asyncio.TimeoutError:
                print("[Async Child] Timeout waiting for request")
                continue  # go back and recv again

            cmd = msg.get("cmd")

            # 2) dispatch + error‐handling
            try:
                if cmd == "__terminate__":
                    break

                if cmd == "__ping__":
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

        self.close()

    def close(self) -> None:
        """Closes the socket."""
        self.sock.close()
        self.ctx.term()
