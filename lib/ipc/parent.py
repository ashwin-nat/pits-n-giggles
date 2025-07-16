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

import zmq
from typing import Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcParent:
    """
    Synchronous ZeroMQ REQ socket client.
    Used by parent process to send command and receive response.
    """

    def __init__(self, port: int, timeout_ms: int = 5000):
        """
        :param port: Port to connect to.
        :param timeout_ms: Receive timeout in milliseconds.
        """
        self.endpoint = f"tcp://127.0.0.1:{port}"
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.REQ)
        self.sock.connect(self.endpoint)
        self.sock.setsockopt(zmq.RCVTIMEO, timeout_ms)
        self.sock.setsockopt(zmq.LINGER, 0)

    def request(self, command: str, args: Optional[dict] = None) -> dict:
        """
        Sends a command to the child and waits for response.
        Returns a dict, or {'error': ...} if timeout or failure occurs.
        """
        try:
            self.sock.send_json({"cmd": command, "args": args or {}})
            return self.sock.recv_json()
        except zmq.ZMQError as e:
            return {"error": str(e)}

    def close(self) -> None:
        self.sock.close()
        self.ctx.term()
