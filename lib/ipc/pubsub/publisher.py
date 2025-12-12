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
import orjson
from typing import Optional
import logging

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ZmqAsyncPublisher:
    """
    Async publisher sending multipart messages:
        [topic_bytes, payload_bytes]

    - Writes connect to broker's XSUB.
    - publish(topic, dict) is awaitable.
    - Non-blocking send, drops if HWM exceeded.
    - Requires asyncio; uses DONTWAIT.
    """

    def __init__(
        self,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if port is None:
            raise ValueError("ZmqAsyncPublisher requires explicit port")

        self.host = host
        self.port = port
        self.logger = logger
        self._context = zmq.Context.instance()
        self.socket = self._context.socket(zmq.PUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDHWM, 1)

        endpoint = f"tcp://{host}:{port}"
        self.socket.connect(endpoint)

        if self.logger:
            self.logger.info(f"ZmqAsyncPublisher connected to {endpoint}")

    async def publish(self, topic: str, data: dict):
        topic_bytes = topic.encode("utf-8")
        payload = orjson.dumps(data)

        try:
            # Non-blocking send
            self.socket.send_multipart([topic_bytes, payload], flags=zmq.DONTWAIT)
        except zmq.Again:
            if self.logger:
                self.logger.debug("ZmqAsyncPublisher dropped message (HWM full)")

    async def close(self):
        try:
            self.socket.close(linger=0)
        except Exception:
            pass
        if self.logger:
            self.logger.info("ZmqAsyncPublisher closed")

