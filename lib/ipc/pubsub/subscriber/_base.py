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
import time
from typing import Awaitable, Callable, Dict, Generic, Optional, Tuple, TypeVar

import orjson
import zmq

from lib.event_counter import EventCounter

# -------------------------------------- TYPES -------------------------------------------------------------------------

OnConnectCbAsync = Callable[[], Awaitable[None]]
OnDisconnectCbAsync = Callable[[Exception | None], Awaitable[None]]

_JsonHandlerT = TypeVar("_JsonHandlerT", Callable[[dict], None], Callable[[dict], Awaitable[None]])
_RawHandlerT  = TypeVar("_RawHandlerT",  Callable[[bytes], None], Callable[[bytes], Awaitable[None]])

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class _IpcSubscriberStats:
    """Envelope parsing, sequencing, and stats tracking."""

    def __init__(self) -> None:
        self._last_message_id_by_topic: Dict[str, int] = {}
        self.stats = EventCounter()

    def _track_missed_messages(self, topic: str, count: int) -> None:
        self.stats.track_event("__TOTAL__", "__MISSED__", count=count)
        self.stats.track_event(topic, "__MISSED__", count=count)

    def _parse_envelope(self, meta_bytes: bytes, payload_bytes: bytes) -> Tuple[str, bytes, int, Optional[int]]:
        meta = orjson.loads(meta_bytes)
        send_ts_ns = meta.get("send_ts_ns")

        if not isinstance(send_ts_ns, int):
            send_ts_ns = None

        content_type = meta.get("content_type", "json")
        return content_type, payload_bytes, meta["message_id"], send_ts_ns

    def _track_latency(
        self, topic: str, send_ts_ns: Optional[int], recv_ts_ns: Optional[int] = None
    ) -> None:
        if send_ts_ns is None:
            return

        if recv_ts_ns is None:
            recv_ts_ns = time.time_ns()

        self.stats.track_packet_latency(
            "__TOTAL__", "__LATENCY__", send_ts_ns, recv_ts_ns
        )
        self.stats.track_packet_latency(
            topic, "__LATENCY__", send_ts_ns, recv_ts_ns
        )

    def _track_sequence(self, topic: str, message_id: int) -> None:
        last_message_id = self._last_message_id_by_topic.get(topic)
        if last_message_id is None:
            self._last_message_id_by_topic[topic] = message_id
            return

        expected_next = last_message_id + 1
        if message_id > expected_next:
            missed = message_id - expected_next
            self._track_missed_messages(topic, missed)
            self.logger.debug(  # type: ignore[attr-defined]
                "Detected %d missed messages on topic %s (expected %d, got %d)",
                missed,
                topic,
                expected_next,
                message_id,
            )
        elif message_id <= last_message_id:
            self.stats.track_event("__TOTAL__", "__SEQ_ANOMALY__")
            self.stats.track_event(topic, "__SEQ_ANOMALY__")

        self._last_message_id_by_topic[topic] = message_id

    def get_stats(self) -> dict:
        """Get current subscriber stats snapshot."""
        return self.stats.get_stats()


class _IpcSubscriberBase(_IpcSubscriberStats, Generic[_JsonHandlerT, _RawHandlerT]):
    """Shared init, socket lifecycle, route registration, and shutdown."""

    def __init__(
        self,
        host: str,
        port: int,
        logger: logging.Logger,
    ) -> None:
        super().__init__()

        self.host = host
        self.port = port
        self.logger = logger

        self._context = zmq.Context()
        self._routes: Dict[str, _JsonHandlerT] = {}
        self._raw_routes: Dict[str, Tuple[str, _RawHandlerT]] = {}
        self._running = False
        self.socket: Optional[zmq.Socket] = None

    def _create_and_connect(self) -> None:
        """Create a new SUB socket and connect to the broker."""
        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        self.socket = self._context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)

        for topic in {**self._routes, **{t: None for t in self._raw_routes}}:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())

        endpoint = f"tcp://{self.host}:{self.port}"
        self.socket.connect(endpoint)
        self.logger.debug("%s configured endpoint %s", type(self).__name__, endpoint)

    def route(self, topic: str) -> Callable[[_JsonHandlerT], _JsonHandlerT]:
        """Register a JSON handler for topic. Raises ValueError if already registered as raw."""
        if topic in self._raw_routes:
            raise ValueError(f"Topic '{topic}' is already registered as a raw route")

        topic_bytes = topic.encode()
        if self.socket:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)

        def decorator(func: _JsonHandlerT) -> _JsonHandlerT:
            self._routes[topic] = func
            return func

        return decorator  # type: ignore[return-value]

    def route_raw(self, topic: str, content_type: str = "binary") -> Callable[[_RawHandlerT], _RawHandlerT]:
        """Register a raw bytes handler for topic. Raises ValueError if already registered as JSON."""
        if topic in self._routes:
            raise ValueError(f"Topic '{topic}' is already registered as a JSON route")

        topic_bytes = topic.encode()
        if self.socket:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)

        def decorator(func: _RawHandlerT) -> _RawHandlerT:
            self._raw_routes[topic] = (content_type, func)
            return func

        return decorator  # type: ignore[return-value]

    def close(self) -> None:
        """Signal the loop to exit."""
        self._running = False
