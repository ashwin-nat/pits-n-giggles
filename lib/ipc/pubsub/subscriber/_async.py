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
from typing import Awaitable, Callable, Optional

import orjson
import zmq

from ._base import OnConnectCbAsync, OnDisconnectCbAsync, _IpcSubscriberBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcSubscriberAsync(
    _IpcSubscriberBase[
        Callable[[dict], Awaitable[None]],
        Callable[[bytes], Awaitable[None]],
    ]
):
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
    ) -> None:
        if port is None:
            raise ValueError("IpcSubscriberAsync requires explicit port")

        if logger is None:
            logger = logging.getLogger(f"{__name__}.IpcSubscriberAsync")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False

        super().__init__(host=host, port=port, logger=logger)

        self._on_connect: Optional[OnConnectCbAsync] = None
        self._on_disconnect: Optional[OnDisconnectCbAsync] = None
        self._connected = False

    # ---------------------------------------------------------
    # Public overrides with concrete types for static analysis
    # ---------------------------------------------------------

    def route(
        self, topic: str
    ) -> Callable[[Callable[[dict], Awaitable[None]]], Callable[[dict], Awaitable[None]]]:
        return super().route(topic)

    def route_raw(
        self, topic: str, content_type: str = "binary"
    ) -> Callable[[Callable[[bytes], Awaitable[None]]], Callable[[bytes], Awaitable[None]]]:
        return super().route_raw(topic, content_type)

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

    async def run(self) -> None:
        poller = zmq.Poller()

        self._create_and_connect()
        poller.register(self.socket, zmq.POLLIN)

        self.logger.debug("IpcSubscriberAsync run loop started")

        self._running = True
        while self._running:
            try:
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
            except Exception as e:  # pylint: disable=broad-except
                self.stats.track_event("__TOTAL__", "__HANDLER_ERR__")
                self.stats.track_event(topic, "__HANDLER_ERR__")
                self.logger.exception("Handler error for topic '%s': %s", topic, e)

        try:
            poller.unregister(self.socket)
        except Exception:  # pylint: disable=broad-except
            pass

        try:
            self.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-except
            pass

        self.logger.debug("IpcSubscriberAsync run loop exited")
        await self._mark_disconnected(None)

    # ------------------------------------------------------------------
    # Connection callbacks
    # ------------------------------------------------------------------

    def on_connect(self, func: OnConnectCbAsync) -> OnConnectCbAsync:
        self._on_connect = func
        return func

    def on_disconnect(self, func: OnDisconnectCbAsync) -> OnDisconnectCbAsync:
        self._on_disconnect = func
        return func

    async def _mark_connected(self) -> None:
        if not self._connected:
            self._connected = True
            if self._on_connect:
                try:
                    await self._on_connect()
                except Exception:  # pylint: disable=broad-except
                    self.logger.exception("Unhandled exception in on_connect callback")

    async def _mark_disconnected(self, exc: Exception | None) -> None:
        if self._connected:
            self._connected = False
            if self._on_disconnect:
                try:
                    await self._on_disconnect(exc)
                except Exception:  # pylint: disable=broad-except
                    self.logger.exception("Unhandled exception in on_disconnect callback")

    @property
    def is_connected(self) -> bool:
        return self._connected
