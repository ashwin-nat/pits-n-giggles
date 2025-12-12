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
    Synchronous consumer with route(topic) decorator.

    Usage:
        consumer = ZmqConsumer(host, port)

        @consumer.route("telemetry")
        def handle_telemetry(data): ...

        consumer.start()   # blocking
    """

    def __init__(
        self,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if port is None:
            raise ValueError("ZmqConsumer requires explicit port")

        self.host = host
        self.port = port
        self.logger = logger
        self._context = zmq.Context.instance()

        self.socket = self._context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)

        self._routes: Dict[str, Callable[[dict], None]] = {}

        endpoint = f"tcp://{host}:{port}"
        self.socket.connect(endpoint)

        self._running = False

        if self.logger:
            self.logger.info(f"ZmqConsumer connected to {endpoint}")

    def route(self, topic: str):
        """
        Decorator — registers a handler and subscribes to the topic.
        """

        topic_bytes = topic.encode("utf-8")
        self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)

        def decorator(func: Callable[[dict], None]):
            self._routes[topic] = func
            return func

        return decorator

    def start(self):
        """Blocking dispatch loop."""
        self._running = True
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        if self.logger:
            self.logger.info("ZmqConsumer started")

        while self._running:
            events = dict(poller.poll(100))  # 100 ms timeout for clean shutdown

            if self.socket in events:
                topic_bytes, payload = self.socket.recv_multipart()
                topic = topic_bytes.decode("utf-8")
                data = orjson.loads(payload)

                handler = self._routes.get(topic)
                if handler:
                    try:
                        handler(data)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Handler error for topic={topic}: {e}")

        if self.logger:
            self.logger.info("ZmqConsumer stopped")

    def close(self):
        self._running = False
        try:
            self.socket.close(linger=0)
        except Exception:
            pass
        if self.logger:
            self.logger.info("ZmqConsumer closed")
