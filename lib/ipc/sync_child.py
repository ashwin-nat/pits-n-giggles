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

import threading
import zmq
from typing import Callable, Awaitable, Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcChildSync:
    """
    Synchronous ZeroMQ REP socket server.
    Used by child process to handle requests synchronously.
    Can be run in a dedicated thread.
    """

    def __init__(self, port: int, name: str = "IpcChildSync"):
        """
        :param port: Port to bind to.
        :param name: Name of the child process.
        """
        self.name = name
        self.endpoint = f"tcp://127.0.0.1:{port}"
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.REP)
        self.sock.bind(self.endpoint)
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def serve(self, handler_fn: Callable[[dict], dict]) -> None:
        """
        Starts the request loop. Calls handler_fn on each request.
        If handler_fn returns, the response is sent to parent.
        Stops if a 'quit' command is received.
        """
        self._running = True
        while self._running:
            try:
                msg = self.sock.recv_json()
                cmd = msg.get("cmd")
                if cmd == "__terminate__":
                    self._running = False
                    break
                if cmd == "__ping__":
                    response = {"reply": "__pong__", "source": self.name}
                    self.sock.send_json(response)
                    continue

                response = handler_fn(msg)
                self.sock.send_json(response)
            except Exception as e:
                self.sock.send_json({"error": str(e)})

        self.close()

    def serve_in_thread(self, handler_fn: Callable[[dict], dict]) -> None:
        """
        Starts the serve loop in a background thread.
        """
        self._thread = threading.Thread(target=self.serve, args=(handler_fn,), daemon=True)
        self._thread.start()

    def close(self) -> None:
        self.sock.close()
        self.ctx.term()
