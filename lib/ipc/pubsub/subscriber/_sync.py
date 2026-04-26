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
from typing import Callable, Dict, Optional, Tuple

import orjson
import zmq

from ._base import _IpcSubscriberBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcSubscriberSync(
    _IpcSubscriberBase[
        Callable[[dict], None],
        Callable[[bytes], None],
    ]
):
    """Auto-reconnecting synchronous subscriber. Survivable across broker restarts."""

    def __init__(
        self,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if port is None:
            raise ValueError("IpcSubscriberSync requires explicit port")

        if logger is None:
            logger = logging.getLogger(f"{__name__}.IpcSubscriberSync")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False

        super().__init__(host=host, port=port, logger=logger)
        self._create_and_connect()

    # ---------------------------------------------------------
    # Public overrides with concrete types for static analysis
    # ---------------------------------------------------------

    def route(self, topic: str) -> Callable[[Callable[[dict], None]], Callable[[dict], None]]:
        return super().route(topic)

    def route_raw(
        self, topic: str, content_type: str = "binary"
    ) -> Callable[[Callable[[bytes], None]], Callable[[bytes], None]]:
        return super().route_raw(topic, content_type)

    # ---------------------------------------------------------
    # Main loop with auto-reconnect
    # ---------------------------------------------------------

    def start(self) -> None:
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
                latest_per_topic: Dict[str, Tuple[str, bytes]] = {}
                recv_failed = False

                while True:
                    try:
                        frames = self.socket.recv_multipart(flags=zmq.DONTWAIT)
                    except zmq.Again:
                        break
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

        try:
            poller.unregister(self.socket)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            self.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self.logger.debug("IpcSubscriberSync stopped")
