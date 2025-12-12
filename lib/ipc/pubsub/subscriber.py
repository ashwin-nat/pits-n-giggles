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
from typing import Callable, Dict, Optional
import logging

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

        self._context = zmq.Context.instance()
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

        self.logger.info(f"IpcSubscriberSync connected to {endpoint}")

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

        while self._running:

            poller.register(self.socket, zmq.POLLIN)

            try:
                events = dict(poller.poll(100))
            except zmq.ZMQError:
                # Poll error = socket died -> reconnect
                self.logger.warning("Poll failed — reconnecting SUB socket")
                self._create_and_connect()
                continue

            if self.socket in events:
                try:
                    frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
                except zmq.ZMQError:
                    # Receive error = socket died -> reconnect
                    self.logger.warning("Receive failed — reconnecting SUB socket")
                    self._create_and_connect()
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
                        self.logger.error(f"Handler error for {topic}: {e}")

        # clean shutdown
        try:
            self.socket.close(linger=0)
        except Exception:
            pass

        self.logger.info("IpcSubscriberSync stopped")

    # ---------------------------------------------------------
    # External shutdown
    # ---------------------------------------------------------
    def close(self):
        self._running = False
