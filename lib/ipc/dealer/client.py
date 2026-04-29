# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from typing import Callable, Dict, Optional

import orjson
import zmq

from lib.event_counter import EventCounter

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_REPLY_REQUIRED = b"\x01"
_NO_REPLY       = b"\x00"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcDealerClient:
    """
    Synchronous ZeroMQ DEALER client for receiving routed commands.

    Connects to an IpcRouter with a fixed ZMQ identity. Incoming frames arrive as:
        [sender_id, reply_flag, topic, payload]

    Where reply_flag is:
        b"\\x01" — sender expects a reply (ACK or response data)
        b"\\x00" — fire-and-forget, no reply needed

    The client dispatches to the registered handler. If reply is expected, it
    sends back the handler's return value (or an error dict on exception).
    If fire-and-forget, no reply is sent.

    Usage::

        client = IpcDealerClient(port=53836, identity="hud")

        @client.route("hud-toggle-notification")
        def on_toggle(data: dict):
            overlays_mgr.toggle(data["oid"])
            # no return value needed for fire-and-forget

        @client.route("get-stats")
        def on_get_stats(data: dict) -> dict:
            return overlays_mgr.get_stats()  # returned to sender

        threading.Thread(target=client.start, daemon=True).start()
        # ... later:
        client.close()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        identity: str = "",
        logger: Optional[logging.Logger] = None,
    ):
        if port is None:
            raise ValueError("IpcDealerClient requires explicit port")
        if not identity:
            raise ValueError("IpcDealerClient requires a non-empty identity")

        self.host = host
        self.port = port
        self.identity = identity

        if logger is None:
            logger = logging.getLogger(f"{__name__}.IpcDealerClient")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self._routes: Dict[str, Callable[[dict], None]] = {}
        self._running = False
        self.stats = EventCounter()

        self._ctx = zmq.Context()
        self.socket: Optional[zmq.Socket] = None
        self._create_and_connect()

    # ---------------------------------------------------------
    # Socket setup
    # ---------------------------------------------------------
    def _create_and_connect(self) -> None:
        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        self.socket = self._ctx.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.IDENTITY, self.identity.encode())
        endpoint = f"tcp://{self.host}:{self.port}"
        self.socket.connect(endpoint)
        self.logger.debug("IpcDealerClient [%s] connected to %s", self.identity, endpoint)

    # ---------------------------------------------------------
    # Register handler
    # ---------------------------------------------------------
    def route(self, topic: str):
        """Decorator to register a handler for a topic string."""
        def decorator(func: Callable[[dict], None]):
            self._routes[topic] = func
            return func
        return decorator

    # ---------------------------------------------------------
    # Main receive loop
    # ---------------------------------------------------------
    def start(self) -> None:
        """Blocking receive loop. Call in a daemon thread."""
        self._running = True
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while self._running:
            try:
                events = dict(poller.poll(100))
            except zmq.ZMQError:
                if not self._running:
                    break
                self.stats.track_event("__ERROR__", "poll_failed")
                self._create_and_connect()
                poller = zmq.Poller()
                poller.register(self.socket, zmq.POLLIN)
                continue

            if self.socket not in events:
                continue

            try:
                frames = self.socket.recv_multipart(flags=zmq.NOBLOCK)
            except zmq.Again:
                continue
            except zmq.ZMQError:
                if not self._running:
                    break
                self.stats.track_event("__ERROR__", "recv_failed")
                self._create_and_connect()
                poller = zmq.Poller()
                poller.register(self.socket, zmq.POLLIN)
                continue

            # Router delivers: [sender_id, reply_flag, topic, payload]
            if len(frames) < 4:
                self.stats.track_event("__DROP__", "short_frame")
                continue

            sender_id, reply_flag, topic_bytes, payload_bytes = (
                frames[0], frames[1], frames[2], frames[3]
            )
            wants_reply = (reply_flag == _REPLY_REQUIRED)
            topic = topic_bytes.decode("utf-8", errors="replace")
            total_size = sum(len(f) for f in frames)

            self.stats.track_packet("__INCOMING__", topic, total_size)

            try:
                data = orjson.loads(payload_bytes)
            except (ValueError, TypeError):
                self.stats.track_event("__DROP__", "invalid_json")
                if wants_reply:
                    self._send_reply(sender_id, {"status": "error", "reason": "invalid payload"})
                continue

            handler = self._routes.get(topic)
            if handler is None:
                self.stats.track_event("__DROP__", f"unrouted_{topic}")
                if wants_reply:
                    self._send_reply(sender_id, {"status": "error", "reason": f"unknown topic: {topic}"})
                continue

            try:
                result = handler(data)
                self.stats.track_event("__HANDLER_OK__", topic)
                if wants_reply:
                    reply = result if isinstance(result, dict) else {"status": "ok"}
                    self._send_reply(sender_id, reply)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.stats.track_event("__HANDLER_ERR__", topic)
                self.logger.exception("Handler error for topic %r: %s", topic, e)
                if wants_reply:
                    self._send_reply(sender_id, {"status": "error", "reason": str(e)})

        try:
            poller.unregister(self.socket)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            self.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self.logger.debug("IpcDealerClient [%s] stopped", self.identity)

    def _send_reply(self, sender_id: bytes, reply: dict) -> None:
        try:
            self.socket.send_multipart(
                [sender_id, orjson.dumps(reply)],
                flags=zmq.NOBLOCK,
            )
            self.stats.track_event("__REPLY__", reply.get("status", "data"))
        except zmq.ZMQError as e:
            self.stats.track_event("__ERROR__", "reply_send_failed")
            self.logger.warning("IpcDealerClient [%s] failed to send reply: %s", self.identity, e)

    # ---------------------------------------------------------
    # Shutdown / stats
    # ---------------------------------------------------------
    def close(self) -> None:
        """Signal the receive loop to stop."""
        self._running = False

    def get_stats(self) -> dict:
        return self.stats.get_stats()
