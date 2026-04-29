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
import threading
import time
from typing import Optional

import zmq

from lib.error_status import PngRouterPortInUseError
from lib.event_counter import EventCounter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcRouterBroker:
    """
    ZeroMQ ROUTER broker for lossless point-to-point command delivery.

    DEALER clients connect with a fixed ZMQ identity. The broker forwards
    messages between them by swapping the routing envelope:

        Sender sends:    [dest_identity, topic, payload]
        Broker receives: [sender_identity, dest_identity, topic, payload]
        Broker forwards: [dest_identity, sender_identity, topic, payload]

    The recipient replies:
        [sender_identity, ack_payload]
    which the broker routes back as:
        [original_sender_identity, ack_payload]

    Usage::

        broker = IpcRouterBroker(port=53836)
        broker.run_in_thread()
        # ... later:
        broker.close()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        logger: Optional[logging.Logger] = None,
        name: str = "IpcRouterBroker",
    ):
        self.host = host
        self.name = name

        if logger is None:
            logger = logging.getLogger(f"{__name__}")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self.stats = EventCounter()
        self._start_time = time.time()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._ctx = zmq.Context()
        self._sock: zmq.Socket = self._ctx.socket(zmq.ROUTER)
        self._sock.setsockopt(zmq.LINGER, 0)
        # Allow reconnecting clients with the same identity
        self._sock.setsockopt(zmq.ROUTER_HANDOVER, 1)

        try:
            self._sock.bind(f"tcp://{self.host}:{port}")
        except zmq.ZMQError as e:
            self._sock.close(linger=0)
            self._ctx.term()
            if e.errno == zmq.EADDRINUSE:
                raise PngRouterPortInUseError(
                    f"{self.name}: ROUTER port already in use ({port})"
                ) from e
            raise

        self.port = int(self._sock.getsockopt(zmq.LAST_ENDPOINT).split(b":")[-1])

        self.logger.debug("%s bound on tcp://%s:%d", self.name, self.host, self.port)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Blocking forward loop. Run in a daemon thread via run_in_thread()."""
        self.logger.debug("%s router loop starting", self.name)
        poller = zmq.Poller()
        poller.register(self._sock, zmq.POLLIN)

        while not self._stop_event.is_set():
            try:
                events = dict(poller.poll(timeout=100))
            except zmq.ZMQError:
                if self._stop_event.is_set():
                    break
                self.stats.track_event("__ERROR__", "poll_failed")
                continue

            if self._sock not in events:
                continue

            try:
                frames = self._sock.recv_multipart(flags=zmq.NOBLOCK)
            except zmq.Again:
                continue
            except zmq.ZMQError:
                if self._stop_event.is_set():
                    break
                self.stats.track_event("__ERROR__", "recv_failed")
                continue

            # ROUTER socket prepends sender identity automatically.
            # Command layout (sender → dest): [sender_id, dest_id, topic, payload...]
            # ACK reply layout (dest → sender): [sender_id, dest_id, ack_payload]
            # In both cases we swap the first two frames to route back.
            if len(frames) < 3:
                self.stats.track_event("__DROP__", "short_frame")
                self.logger.debug("%s dropped short frame (%d parts)", self.name, len(frames))
                continue

            sender_id, dest_id, *rest = frames
            total_size = sum(len(f) for f in frames)
            topic = rest[0].decode("utf-8", errors="replace") if rest else ""

            # Forward: [dest_id, sender_id, rest...]
            try:
                self._sock.send_multipart(
                    [dest_id, sender_id] + rest,
                    flags=zmq.NOBLOCK,
                )
                self.stats.track_packet("__FORWARD__", topic, total_size)
                self.logger.debug(
                    "%s routed %r → %r",
                    self.name,
                    sender_id,
                    dest_id,
                )
            except zmq.Again:
                self.stats.track_event("__DROP__", "hwm_full")
            except zmq.ZMQError as e:
                self.stats.track_event("__ERROR__", "send_failed")
                self.logger.warning("%s send error: %s", self.name, e)

        self.logger.debug("%s router loop exited", self.name)

    def run_in_thread(self, name: str = "IPC-Router") -> threading.Thread:
        """Start the broker loop in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return self._thread

        self._stop_event.clear()
        self._thread = threading.Thread(target=self.run, daemon=True, name=name)
        self._thread.start()
        return self._thread

    def get_stats(self) -> dict:
        """Return a stats snapshot."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            **self.stats.get_stats(),
        }

    def close(self) -> None:
        """Signal the loop to stop and close the socket."""
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=0.5)

        try:
            self._sock.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            self._ctx.term()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self.logger.debug("%s closed", self.name)
