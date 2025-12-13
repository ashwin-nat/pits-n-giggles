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
import logging
from typing import Optional

import orjson
import zmq

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcPublisherAsync:
    """
    Async, auto-reconnecting ZeroMQ PUB publisher.

    - Never blocks event loop
    - Reconnects when broker restarts
    - publish() is always non-blocking
    - Drops messages while disconnected (PUB/SUB semantics)
    """

    RECONNECT_MIN_DELAY = 0.05
    RECONNECT_MAX_DELAY = 1.0

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if port is None:
            raise ValueError("IpcPublisherAsync requires explicit port")

        self.host = host
        self.port = port
        if logger is None:
            logger = logging.getLogger(f"{__name__}.IpcPublisherAsync")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self._context = zmq.Context.instance()
        self.socket: Optional[zmq.Socket] = None

        self._connected = False
        self._running = True
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    # ---------------------------------------------------------
    # Socket creation
    # ---------------------------------------------------------
    def _create_socket(self) -> zmq.Socket:
        sock: zmq.Socket = self._context.socket(zmq.PUB)
        sock.setsockopt(zmq.LINGER, 0)
        sock.setsockopt(zmq.SNDHWM, 1)
        sock.connect(f"tcp://{self.host}:{self.port}")
        return sock

    # ---------------------------------------------------------
    # Async reconnect loop (non-blocking)
    # ---------------------------------------------------------
    async def _reconnect_loop(self):
        delay = self.RECONNECT_MIN_DELAY

        while self._running:
            if not self._connected:
                try:
                    self.socket = self._create_socket()
                    self._connected = True
                    delay = self.RECONNECT_MIN_DELAY

                    self.logger.debug(f"IpcPublisherAsync connected to tcp://{self.host}:{self.port}")

                except Exception:
                    self._connected = False
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.RECONNECT_MAX_DELAY)
                    continue

            # Connected -> idle until publish() marks us disconnected
            await asyncio.sleep(0.05)

    # ---------------------------------------------------------
    # Publish
    # ---------------------------------------------------------
    async def publish(self, topic: str, data: dict):
        if not self._connected:
            return  # drop silently (ZeroMQ semantics)

        topic_bytes = topic.encode("utf-8")
        payload = orjson.dumps(data)

        try:
            self.socket.send_multipart([topic_bytes, payload], flags=zmq.DONTWAIT)

        except zmq.Again:
            # HWM full -> drop silently
            self.logger.debug("IpcPublisherAsync dropped message (HWM full)")

        except zmq.ZMQError:
            # Socket died -> mark disconnected, reconnect loop will fix
            self._connected = False
            try:
                self.socket.close(linger=0)
            except:
                pass

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------
    async def close(self):
        self._running = False
        if self._reconnect_task:
            self._reconnect_task.cancel()

        if self.socket:
            try:
                self.socket.close(linger=0)
            except:
                pass

        self.logger.debug("IpcPublisherAsync closed")
