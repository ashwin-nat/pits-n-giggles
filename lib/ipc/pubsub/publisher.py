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
import time
from typing import Dict, Optional

import orjson
import zmq

from lib.event_counter import EventCounter

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

        self._context = zmq.Context()
        self.socket: Optional[zmq.Socket] = None

        self._connected = False
        self._running = True
        self._reconnect_task = None
        self._topic_message_ids: Dict[str, int] = {}
        self.stats = EventCounter()

    def get_task(self) -> asyncio.Task:
        """
        Return the reconnect loop task.

        Caller is responsible for scheduling and lifetime management.
        """
        if self._reconnect_task:
            return self._reconnect_task

        self._reconnect_task = asyncio.create_task(
            self._reconnect_loop(),
            name="IpcPublisherAsync.reconnect",
        )
        return self._reconnect_task

    async def start(self):
        self.get_task()

    # ---------------------------------------------------------
    # Socket creation
    # ---------------------------------------------------------
    def _create_socket(self) -> zmq.Socket:
        sock: zmq.Socket = self._context.socket(zmq.PUB)
        sock.setsockopt(zmq.LINGER, 0)
        # SNDHWM=3: At 30Hz (33ms/frame), a value of 1 caused ~10% silent kernel-level drops
        # (never surfacing as zmq.Again). 3 gives enough slack for scheduler jitter while
        # still discarding stale frames under genuine backpressure.
        sock.setsockopt(zmq.SNDHWM, 3)
        endpoint = f"tcp://{self.host}:{self.port}"
        sock.connect(endpoint)
        self.logger.debug("IpcPublisherAsync configured endpoint %s", endpoint)
        return sock

    # ---------------------------------------------------------
    # Async reconnect loop (non-blocking)
    # ---------------------------------------------------------
    async def _reconnect_loop(self):
        delay = self.RECONNECT_MIN_DELAY

        while self._running:
            if not self._connected:
                try:
                    self.stats.track_event("__RECONNECT__", "attempt")
                    self.socket = self._create_socket()
                    self._connected = True
                    delay = self.RECONNECT_MIN_DELAY
                    self.stats.track_event("__RECONNECT__", "success")

                except Exception:  # pylint: disable=broad-except
                    self._connected = False
                    self.stats.track_event("__RECONNECT__", "failure")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.RECONNECT_MAX_DELAY)
                    continue

            # Connected -> idle until publish() marks us disconnected
            await asyncio.sleep(0.05)

    # ---------------------------------------------------------
    # Message envelope helpers
    # ---------------------------------------------------------
    def _next_message_id(self, topic: str) -> int:
        current = self._topic_message_ids.get(topic, 0) + 1
        self._topic_message_ids[topic] = current
        return current

    def _build_envelope(self, topic: str, data: dict) -> dict:
        return {
            "__meta__": {
                "message_id": self._next_message_id(topic),
                "send_ts_ns": time.time_ns(),
            },
            "__payload__": data,
        }

    # ---------------------------------------------------------
    # Publish
    # ---------------------------------------------------------
    async def publish(self, topic: str, data: dict):
        envelope = self._build_envelope(topic, data)

        if not self._connected:
            self.stats.track_event("__DROP__", "disconnected")
            self.stats.track_event("__DROP_TOPIC__", topic)
            return  # drop silently (ZeroMQ semantics)

        topic_bytes = topic.encode("utf-8")
        payload = orjson.dumps(envelope)
        total_size = len(topic_bytes) + len(payload)

        try:
            self.socket.send_multipart([topic_bytes, payload], flags=zmq.DONTWAIT)
            self.stats.track_packet("__OUTGOING__", "__TOTAL__", total_size)
            self.stats.track_packet("__TOPIC_OUTGOING__", topic, total_size)

        except zmq.Again:
            # HWM full -> drop silently
            self.stats.track_packet("__DROP_HWM__", "__TOTAL__", total_size)
            self.stats.track_packet("__DROP_HWM_TOPIC__", topic, total_size)
            self.logger.debug("IpcPublisherAsync dropped message (HWM full)")

        except zmq.ZMQError:
            # Socket died -> mark disconnected, reconnect loop will fix
            self._connected = False
            self.stats.track_event("__ERROR__", "send_zmq_error")
            self.stats.track_packet("__DROP_ZMQ_ERROR__", "__TOTAL__", total_size)
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

    def get_stats(self) -> dict:
        """Get current publisher stats snapshot."""
        return self.stats.get_stats()
