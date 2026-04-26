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
from typing import Awaitable, Callable, Dict, Optional, Tuple

import orjson
import zmq

from lib.event_counter import EventCounter

# -------------------------------------- TYPES -------------------------------------------------------------------------

OnConnectCbAsync = Callable[[], Awaitable[None]]
OnDisconnectCbAsync = Callable[[Exception | None], Awaitable[None]]

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class _IpcSubscriberStats:
    """Shared envelope parsing, sequencing, and stats tracking for sync/async subscribers."""

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


class IpcSubscriberSync(_IpcSubscriberStats):
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
        super().__init__()

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
        self._raw_routes: Dict[str, Tuple[str, Callable[[bytes], None]]] = {}

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
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        self.socket: zmq.Socket = self._context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)

        # Restore all topic subscriptions
        for topic in {**self._routes, **{t: None for t in self._raw_routes}}:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.encode())

        endpoint = f"tcp://{self.host}:{self.port}"
        self.socket.connect(endpoint)

        self.logger.debug("IpcSubscriberSync configured endpoint %s", endpoint)

    # ---------------------------------------------------------
    # Register handlers
    # ---------------------------------------------------------
    def route(self, topic: str):
        """Register a JSON handler for topic. Raises ValueError if already registered as raw."""
        if topic in self._raw_routes:
            raise ValueError(f"Topic '{topic}' is already registered as a raw route")

        topic_bytes = topic.encode()
        if self.socket:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)

        def decorator(func: Callable[[dict], None]):
            self._routes[topic] = func
            return func

        return decorator

    def route_raw(self, topic: str, content_type: str = "binary"):
        """Register a raw bytes handler for topic. Raises ValueError if already registered as JSON."""
        if topic in self._routes:
            raise ValueError(f"Topic '{topic}' is already registered as a JSON route")

        topic_bytes = topic.encode()
        if self.socket:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)

        def decorator(func: Callable[[bytes], None]):
            self._raw_routes[topic] = (content_type, func)
            return func

        return decorator

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
                # Drain all queued messages, keeping only the latest per topic.
                # PUB/SUB semantics: consumers only need the freshest state.
                latest_per_topic: Dict[str, Tuple[str, bytes]] = {}
                recv_failed = False

                while True:
                    try:
                        frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
                    except zmq.Again:
                        break  # socket drained
                    except zmq.ZMQError:
                        self.stats.track_event("__ERROR__", "recv_failed")
                        self.logger.warning("Receive failed - reconnecting SUB socket")
                        self._create_and_connect()
                        poller = zmq.Poller()
                        poller.register(self.socket, zmq.POLLIN)
                        recv_failed = True
                        break

                    if len(frames) != 3:
                        self.stats.track_event("__DROP__", "invalid_frame_count")
                        continue

                    topic_bytes, meta_bytes, payload_bytes = frames
                    topic = topic_bytes.decode()
                    total_size = len(topic_bytes) + len(meta_bytes) + len(payload_bytes)

                    self.stats.track_packet("__TOTAL__", "__PACKETS__", total_size)
                    self.stats.track_packet(topic, "__PACKETS__", total_size)

                    if topic not in self._routes and topic not in self._raw_routes:
                        self.stats.track_event("__DROP__", f"unrouted_topic_{topic}")
                        continue

                    try:
                        content_type, raw_payload, message_id, send_ts_ns = self._parse_envelope(
                            meta_bytes, payload_bytes
                        )
                        self._track_sequence(topic, message_id)
                        self._track_latency(topic, send_ts_ns, recv_ts_ns=time.time_ns())
                    except (ValueError, TypeError, KeyError):
                        self.stats.track_event("__DROP__", "invalid_envelope")
                        continue

                    if topic in self._routes:
                        if content_type != "json":
                            self.stats.track_event("__DROP__", f"wrong_content_type_for_json_route_{topic}")
                            continue
                    else:
                        expected_ct, _ = self._raw_routes[topic]
                        if content_type != expected_ct:
                            self.stats.track_event("__DROP__", f"wrong_content_type_for_raw_route_{topic}")
                            continue

                    if topic in latest_per_topic:
                        self.stats.track_event("__TOTAL__", "__STALE_DROP__")
                        self.stats.track_event(topic, "__STALE_DROP__")

                    latest_per_topic[topic] = (content_type, raw_payload)

                if recv_failed:
                    continue

                for topic, (content_type, raw_payload) in latest_per_topic.items():
                    try:
                        if topic in self._routes:
                            handler = self._routes[topic]
                            handler(orjson.loads(raw_payload))
                        else:
                            _, handler = self._raw_routes[topic]
                            handler(raw_payload)
                        self.stats.track_event("__TOTAL__", "__HANDLER_OK__")
                        self.stats.track_event(topic, "__HANDLER_OK__")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        self.stats.track_event("__TOTAL__", "__HANDLER_ERR__")
                        self.stats.track_event(topic, "__HANDLER_ERR__")
                        self.logger.exception("Handler error for %s: %s", topic, e)

        # clean shutdown
        try:
            poller.unregister(self.socket)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            self.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self.logger.debug("IpcSubscriberSync stopped")

    # ---------------------------------------------------------
    # External shutdown
    # ---------------------------------------------------------
    def close(self):
        self._running = False

class IpcSubscriberAsync(_IpcSubscriberStats):
    """
    Async, auto-reconnecting ZeroMQ SUB subscriber.

    - Caller owns the asyncio.Task
    - run() is a long-lived coroutine
    - Survives broker restarts
    - Topic → async handler routing
    """

    RECONNECT_DELAY = 0.2

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__()

        if port is None:
            raise ValueError("IpcSubscriberAsync requires explicit port")

        self.host = host
        self.port = port

        if logger is None:
            logger = logging.getLogger(f"{__name__}.IpcSubscriberAsync")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self._context = zmq.Context()
        self.socket: Optional[zmq.Socket] = None

        self._routes: Dict[str, Callable[[dict], Awaitable[None]]] = {}
        self._raw_routes: Dict[str, Tuple[str, Callable[[bytes], Awaitable[None]]]] = {}
        self._running = True

        self._on_connect: Optional[OnConnectCbAsync] = None
        self._on_disconnect: Optional[OnDisconnectCbAsync] = None
        self._connected = False

    # ------------------------------------------------------------------
    # Socket lifecycle
    # ------------------------------------------------------------------

    def _create_and_connect(self):
        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception: # pylint: disable=broad-except
                pass

        sock = self._context.socket(zmq.SUB)
        sock.setsockopt(zmq.LINGER, 0)

        # Restore subscriptions
        for topic in {**self._routes, **{t: None for t in self._raw_routes}}:
            sock.setsockopt(zmq.SUBSCRIBE, topic.encode())

        endpoint = f"tcp://{self.host}:{self.port}"
        sock.connect(endpoint)

        self.socket = sock
        self.logger.debug(f"IpcSubscriberAsync connected to {endpoint}")

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def route(self, topic: str):
        """Register a JSON handler for topic. Raises ValueError if already registered as raw."""
        if topic in self._raw_routes:
            raise ValueError(f"Topic '{topic}' is already registered as a raw route")

        topic_bytes = topic.encode()

        def decorator(func: Callable[[dict], Awaitable[None]]):
            self._routes[topic] = func
            if self.socket:
                self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)
            return func

        return decorator

    def route_raw(self, topic: str, content_type: str = "binary"):
        """Register a raw bytes handler for topic. Raises ValueError if already registered as JSON."""
        if topic in self._routes:
            raise ValueError(f"Topic '{topic}' is already registered as a JSON route")

        topic_bytes = topic.encode()

        def decorator(func: Callable[[bytes], Awaitable[None]]):
            self._raw_routes[topic] = (content_type, func)
            if self.socket:
                self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)
            return func

        return decorator

    # ------------------------------------------------------------------
    # Main async loop (caller schedules this)
    # ------------------------------------------------------------------

    async def _reconnect(self, poller: zmq.Poller, exc: Exception | None) -> zmq.Poller:
        """Disconnect, wait, recreate socket, return a fresh poller."""
        await self._mark_disconnected(exc)
        await asyncio.sleep(self.RECONNECT_DELAY)
        self._create_and_connect()
        new_poller = zmq.Poller()
        new_poller.register(self.socket, zmq.POLLIN)
        return new_poller

    async def run(self):
        poller = zmq.Poller()

        self._create_and_connect()
        poller.register(self.socket, zmq.POLLIN)

        self.logger.debug("IpcSubscriberAsync run loop started")

        while self._running:
            try:
                # offload blocking poll - extra thread safety is not required
                # since the handlers will still execute on the main event loop
                events = dict(await asyncio.to_thread(poller.poll, 100))
            except zmq.ZMQError as e:
                self.stats.track_event("__ERROR__", "poll_failed")
                self.logger.warning("Poll failed — reconnecting SUB socket")
                poller = await self._reconnect(poller, e)
                continue

            if self.socket not in events:
                await asyncio.sleep(0)
                continue

            try:
                frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
            except zmq.Again:
                continue
            except zmq.ZMQError as e:
                self.stats.track_event("__ERROR__", "recv_failed")
                self.logger.warning("Receive failed — reconnecting SUB socket")
                poller = await self._reconnect(poller, e)
                continue

            if len(frames) != 3:
                self.stats.track_event("__DROP__", "invalid_frame_count")
                continue

            topic_bytes, meta_bytes, payload_bytes = frames
            topic = topic_bytes.decode()
            total_size = len(topic_bytes) + len(meta_bytes) + len(payload_bytes)

            self.stats.track_packet("__TOTAL__", "__PACKETS__", total_size)
            self.stats.track_packet(topic, "__PACKETS__", total_size)

            await self._mark_connected()

            if topic not in self._routes and topic not in self._raw_routes:
                self.stats.track_event("__DROP__", f"unrouted_topic_{topic}")
                continue

            try:
                content_type, raw_payload, message_id, send_ts_ns = self._parse_envelope(
                    meta_bytes, payload_bytes
                )
                self._track_sequence(topic, message_id)
                self._track_latency(topic, send_ts_ns, recv_ts_ns=time.time_ns())
            except (ValueError, TypeError, KeyError):
                self.stats.track_event("__DROP__", "invalid_envelope")
                continue

            if topic in self._routes:
                if content_type != "json":
                    self.stats.track_event("__DROP__", f"wrong_content_type_for_json_route_{topic}")
                    continue
                handler = self._routes[topic]
                payload = orjson.loads(raw_payload)
            else:
                expected_ct, handler = self._raw_routes[topic]
                if content_type != expected_ct:
                    self.stats.track_event("__DROP__", f"wrong_content_type_for_raw_route_{topic}")
                    continue
                payload = raw_payload

            try:
                await handler(payload)
                self.stats.track_event("__TOTAL__", "__HANDLER_OK__")
                self.stats.track_event(topic, "__HANDLER_OK__")
            except Exception as e: # pylint: disable=broad-except
                self.stats.track_event("__TOTAL__", "__HANDLER_ERR__")
                self.stats.track_event(topic, "__HANDLER_ERR__")
                self.logger.exception("Handler error for topic '%s': %s", topic, e)

        # graceful exit
        try:
            poller.unregister(self.socket)
        except Exception: # pylint: disable=broad-except
            pass

        try:
            self.socket.close(linger=0)
        except Exception: # pylint: disable=broad-except
            pass

        self.logger.debug("IpcSubscriberAsync run loop exited")
        await self._mark_disconnected(None)

    # ------------------------------------------------------------------
    # Shutdown signal
    # ------------------------------------------------------------------

    def close(self):
        """Signal the run() loop to exit."""
        self._running = False

    # ------------------------------------------------------------------
    # Connection callbacks
    # ------------------------------------------------------------------

    def on_connect(self, func: OnConnectCbAsync) -> OnConnectCbAsync:
        self._on_connect = func
        return func

    def on_disconnect(self, func: OnDisconnectCbAsync) -> OnDisconnectCbAsync:
        self._on_disconnect = func
        return func

    async def _mark_connected(self):
        if not self._connected:
            self._connected = True
            if self._on_connect:
                try:
                    await self._on_connect()
                except Exception: # pylint: disable=broad-except
                    self.logger.exception("Unhandled exception in on_connect callback")

    async def _mark_disconnected(self, exc: Exception | None):
        if self._connected:
            self._connected = False
            if self._on_disconnect:
                try:
                    await self._on_disconnect(exc)
                except Exception: # pylint: disable=broad-except
                    self.logger.exception("Unhandled exception in on_disconnect callback")

    @property
    def is_connected(self) -> bool:
        return self._connected
