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
from typing import Awaitable, Callable, Dict, Optional

import orjson
import zmq

# -------------------------------------- TYPES -------------------------------------------------------------------------

OnConnectCbAsync = Callable[[], Awaitable[None]]
OnDisconnectCbAsync = Callable[[Exception | None], Awaitable[None]]

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
                self.logger.warning("Poll failed — reconnecting SUB socket")
                self._create_and_connect()
                poller = zmq.Poller()
                poller.register(self.socket, zmq.POLLIN)
                continue

            if self.socket in events:
                try:
                    frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
                except zmq.ZMQError:
                    self.logger.warning("Receive failed — reconnecting SUB socket")
                    self._create_and_connect()
                    poller = zmq.Poller()
                    poller.register(self.socket, zmq.POLLIN)
                    continue

                if len(frames) != 2:
                    continue

                topic_bytes, payload = frames
                topic = topic_bytes.decode()

                handler = self._routes.get(topic)
                if handler:
                    try:
                        data = orjson.loads(payload)
                        handler(data)
                    except Exception as e:
                        self.logger.exception(f"Handler error for {topic}: {e}")

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

    # ---------------------------------------------------------
    # External shutdown
    # ---------------------------------------------------------
    def close(self):
        self._running = False

class IpcSubscriberAsync:
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
        for topic in self._routes:
            sock.setsockopt(zmq.SUBSCRIBE, topic.encode())

        endpoint = f"tcp://{self.host}:{self.port}"
        sock.connect(endpoint)

        self.socket = sock
        self.logger.debug(f"IpcSubscriberAsync connected to {endpoint}")

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def route(self, topic: str):
        topic_bytes = topic.encode()

        def decorator(func: Callable[[dict], Awaitable[None]]):
            self._routes[topic] = func
            if self.socket:
                self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)
            return func

        return decorator

    # ------------------------------------------------------------------
    # Main async loop (caller schedules this)
    # ------------------------------------------------------------------

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
                self.logger.warning("Poll failed — reconnecting SUB socket")
                await self._mark_disconnected(e)
                await asyncio.sleep(self.RECONNECT_DELAY)
                self._create_and_connect()
                poller = zmq.Poller()
                poller.register(self.socket, zmq.POLLIN)
                continue

            if self.socket not in events:
                await asyncio.sleep(0)
                continue

            try:
                frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
            except zmq.ZMQError as e:
                self.logger.warning("Receive failed — reconnecting SUB socket")
                await self._mark_disconnected(e)
                await asyncio.sleep(self.RECONNECT_DELAY)
                self._create_and_connect()
                poller = zmq.Poller()
                poller.register(self.socket, zmq.POLLIN)
                continue

            if len(frames) != 2:
                continue

            topic_bytes, payload = frames
            topic = topic_bytes.decode()
            await self._mark_connected()

            handler = self._routes.get(topic)
            if not handler:
                continue

            try:
                data = orjson.loads(payload)
                await handler(data)
            except Exception: # pylint: disable=broad-except
                self.logger.exception(f"Handler error for topic '{topic}'")

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
                await self._on_connect()

    async def _mark_disconnected(self, exc: Exception | None):
        if self._connected:
            self._connected = False
            if self._on_disconnect:
                await self._on_disconnect(exc)

    @property
    def is_connected(self) -> bool:
        return self._connected
