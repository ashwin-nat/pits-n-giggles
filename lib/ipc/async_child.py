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

    async def serve(self, handler_fn: Callable[[dict], Awaitable[dict]], timeout: Optional[int] = None) -> None:
        """
        Starts the async request loop. Calls await handler_fn(msg) on each request.
        Stops if a 'quit' command is received.
        :param handler_fn: Coroutine function to handle commands
        :param timeout: Optional timeout for recv in seconds
        """
        self._running = True

        while self._running:
            try:
                if timeout:
                    msg: dict = await asyncio.wait_for(self.sock.recv_json(), timeout)
                else:
                    msg: dict = await self.sock.recv_json()

                cmd = msg.get("cmd")
                if cmd == "__terminate__":
                    self._running = False
                    break
                if cmd == "__ping__":
                    response = {"reply": "__pong__", "source": self.name}
                    self.sock.send_json(response)
                    continue

                response = await handler_fn(msg)
                await self.sock.send_json(response)

            except asyncio.TimeoutError:
                print("[Async Child] Timeout waiting for request")
            except Exception as e:  # pylint: disable=broad-exception-caught
                await self.sock.send_json({"error": str(e)})

        self.close()

    def get_task(self, handler_fn: Callable[[dict], Awaitable[dict]], timeout: Optional[int] = None) -> asyncio.Task:
        """
        Returns a background asyncio task that runs the serve loop.
        """
        return asyncio.create_task(self.serve(handler_fn, timeout))

    def close(self) -> None:
        self.sock.close()
        self.ctx.term()
