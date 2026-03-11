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

import logging
from typing import Callable, Dict, Optional, Tuple

import orjson
import zmq

from lib.event_counter import EventCounter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcSubscriberSync:
    """
    Auto-reconnecting synchronous subscriber.
    Survivable across broker restarts.
    """

    def __init__(
        self,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if port is None:
            raise ValueError("IpcSubscriberSync requires explicit port")

        self.host = host
        self.port = port
        if logger is None:
            logger = logging.getLogger(f"{__name__}.IpcSubscriberSync")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self._context = zmq.Context()
        self._routes: Dict[str, Callable[[dict], None]] = {}
        self._last_message_id_by_topic: Dict[str, int] = {}
        self.stats = EventCounter()

        self._running = False
        self.socket: Optional[zmq.Socket] = None

        # Create first socket
        self._create_and_connect()

    # ---------------------------------------------------------
    # Socket setup
    # ---------------------------------------------------------
    def _create_and_connect(self):
        """Create a new SUB socket and connect to the broker."""
        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass

        self.socket: zmq.Socket = self._context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)

        # Restore all topic subscriptions
        for topic in self._routes:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())

        endpoint = f"tcp://{self.host}:{self.port}"
        self.socket.connect(endpoint)

        self.logger.debug(f"IpcSubscriberSync configured endpoint {endpoint}")

    # ---------------------------------------------------------
    # Register handler
    # ---------------------------------------------------------
    def route(self, topic: str):
        topic_bytes = topic.encode()

        # Subscribe immediately
        if self.socket:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)

        def decorator(func):
            self._routes[topic] = func
            return func

        return decorator

    # ---------------------------------------------------------
    # Message envelope helpers
    # ---------------------------------------------------------
    def _track_missed_messages(self, topic: str, count: int) -> None:
        for _ in range(count):
            self.stats.track_event("__MISSED__", "__TOTAL__")
            self.stats.track_event("__MISSED_TOPIC__", topic)

    def _parse_envelope(self, payload: bytes) -> Tuple[dict, int]:
        message = orjson.loads(payload)
        return message["__payload__"], message["__meta__"]["message_id"]

    def _track_sequence(self, topic: str, message_id: int) -> None:
        last_message_id = self._last_message_id_by_topic.get(topic)
        if last_message_id is None:
            self._last_message_id_by_topic[topic] = message_id
            return

        expected_next = last_message_id + 1
        if message_id > expected_next:
            missed = message_id - expected_next
            self._track_missed_messages(topic, missed)
            self.logger.warning(
                "Detected %d missed messages on topic %s (expected %d, got %d)",
                missed,
                topic,
                expected_next,
                message_id,
            )
        elif message_id <= last_message_id:
            self.stats.track_event("__SEQ_ANOMALY__", "__TOTAL__")
            self.stats.track_event("__SEQ_ANOMALY_TOPIC__", topic)

        self._last_message_id_by_topic[topic] = message_id

    # ---------------------------------------------------------
    # Main loop with auto-reconnect
    # ---------------------------------------------------------
    def start(self):
        """Blocking loop with reconnection support."""
        self._running = True
        poller = zmq.Poller()

        poller.register(self.socket, zmq.POLLIN)

        while self._running:
            try:
                events = dict(poller.poll(100))
            except zmq.ZMQError:
                self.stats.track_event("__ERROR__", "poll_failed")
                self.logger.warning("Poll failed - reconnecting SUB socket")
                self._create_and_connect()
                poller = zmq.Poller()
                poller.register(self.socket, zmq.POLLIN)
                continue

            if self.socket in events:
                try:
                    frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
                except zmq.ZMQError:
                    self.stats.track_event("__ERROR__", "recv_failed")
                    self.logger.warning("Receive failed - reconnecting SUB socket")
                    self._create_and_connect()
                    poller = zmq.Poller()
                    poller.register(self.socket, zmq.POLLIN)
                    continue

                if len(frames) != 2:
                    self.stats.track_event("__DROP__", "invalid_frame_count")
                    continue

                topic_bytes, payload = frames
                topic = topic_bytes.decode()
                total_size = len(topic_bytes) + len(payload)

                self.stats.track_packet("__INCOMING__", "__TOTAL__", total_size)
                self.stats.track_packet("__TOPIC_INCOMING__", topic, total_size)

                handler = self._routes.get(topic)
                if handler:
                    try:
                        data, message_id = self._parse_envelope(payload)
                        self._track_sequence(topic, message_id)
                    except Exception:
                        self.stats.track_event("__DROP__", "invalid_envelope")
                        self.stats.track_event("__INVALID_ENVELOPE_TOPIC__", topic)
                        continue

                    try:
                        handler(data)
                        self.stats.track_event("__HANDLER__", "success")
                        self.stats.track_event("__HANDLED_TOPIC__", topic)
                    except Exception as e:
                        self.stats.track_event("__ERROR__", "handler_exception")
                        self.stats.track_event("__HANDLER_ERROR_TOPIC__", topic)
                        self.logger.exception(f"Handler error for {topic}: {e}")
                else:
                    self.stats.track_event("__DROP__", "unrouted_topic")
                    self.stats.track_event("__UNROUTED_TOPIC__", topic)

        # clean shutdown
        try:
            poller.unregister(self.socket)
        except Exception:
            pass

        try:
            self.socket.close(linger=0)
        except Exception:
            pass

        self.logger.debug("IpcSubscriberSync stopped")

    def get_stats(self) -> dict:
        """Get current subscriber stats snapshot."""
        return self.stats.get_stats()

    # ---------------------------------------------------------
    # External shutdown
    # ---------------------------------------------------------
    def close(self):
        self._running = False
