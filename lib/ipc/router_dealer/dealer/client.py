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
from typing import Callable, Dict, Optional

import orjson
import zmq

from lib.event_counter import EventCounter

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_REPLY_REQUIRED = b"\x01"
_NO_REPLY       = b"\x00"

# Sentinel pushed through the pipe to tell the loop to exit cleanly.
_CMD_STOP  = b"\xff"
_CMD_FIRE  = b"\x00"
_CMD_SEND  = b"\x01"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcDealerClient:
    """
    Synchronous ZeroMQ DEALER client — bidirectional.

    Connects to an IpcRouter with a fixed ZMQ identity. Incoming frames arrive as:
        [sender_id, reply_flag, topic, payload]

    Where reply_flag is:
        b"\\x01" — sender expects a reply (ACK or response data)
        b"\\x00" — fire-and-forget, no reply needed

    The client dispatches to the registered handler. If reply is expected, it
    sends back the handler's return value (or an error dict on exception).
    If fire-and-forget, no reply is sent.

    Outbound commands:

    **Fire-and-forget**::

        client.fire("backend", "notify", {"msg": "hello"})

    **Request-response** (blocks caller thread until reply or timeout)::

        reply = client.send("backend", "get-stats", {}, timeout=2.0)

    ``send()`` is safe to call from any thread *except* the loop thread itself
    (deadlock). Only one outbound ``send()`` may be in-flight at a time.

    ZMQ sockets are not thread-safe, so outbound sends are marshalled through
    an inproc PAIR pipe that the loop thread drains alongside the DEALER socket.

    Usage::

        client = IpcDealerClient(port=53836, identity="hud")

        @client.route("hud-toggle-notification")
        def on_toggle(data: dict):
            overlays_mgr.toggle(data["oid"])

        @client.route("get-stats")
        def on_get_stats(data: dict) -> dict:
            return overlays_mgr.get_stats()

        threading.Thread(target=client.start, daemon=True).start()
        # ... later:
        reply = client.send("backend", "query", {})
        client.close()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        identity: str = "",
        logger: Optional[logging.Logger] = None,
    ):
        assert port is not None
        assert identity

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

        # Set when the loop thread starts; used by send() to detect deadlock-prone misuse.
        self._loop_thread_id: Optional[int] = None

        self._ctx = zmq.Context()
        self.socket: Optional[zmq.Socket] = None

        # Inproc PAIR pipe: caller thread → loop thread for outbound sends.
        # Use id(self) so multiple instances in the same process don't collide.
        self._pipe_addr = f"inproc://dealer-pipe-{id(self)}"
        self._pipe_write: zmq.Socket = self._ctx.socket(zmq.PAIR)
        self._pipe_write.setsockopt(zmq.LINGER, 0)
        self._pipe_write.bind(self._pipe_addr)

        self._pipe_read: zmq.Socket = self._ctx.socket(zmq.PAIR)
        self._pipe_read.setsockopt(zmq.LINGER, 0)
        self._pipe_read.connect(self._pipe_addr)

        # Serialises all writes to _pipe_write (ZMQ sockets are not thread-safe).
        self._pipe_lock = threading.Lock()
        # Serialises concurrent send() callers (only one in-flight at a time).
        self._send_lock = threading.Lock()
        # Slot for the loop thread to deposit a send() reply.
        self._reply_slot: Optional[dict] = None
        self._reply_event = threading.Event()

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

    def _rebuild_poller(self) -> zmq.Poller:
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        poller.register(self._pipe_read, zmq.POLLIN)
        return poller

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
    # Outbound: fire-and-forget
    # ---------------------------------------------------------
    def fire(self, dest_identity: str, topic: str, data: dict) -> None:
        """
        Send a command and return immediately — no reply is awaited.

        Thread-safe. May be called from any thread including before start().

        Args:
            dest_identity: ZMQ identity of the target DEALER.
            topic: Command topic string.
            data: Payload dict (JSON-serialisable).
        """
        payload = orjson.dumps(data)
        # Push to pipe: [_CMD_FIRE, dest, topic, payload]
        with self._pipe_lock:
            try:
                self._pipe_write.send_multipart(
                    [_CMD_FIRE, dest_identity.encode(), topic.encode(), payload],
                    flags=zmq.NOBLOCK,
                )
            except zmq.ZMQError as e:
                self.stats.track_event("__ERROR__", "fire_pipe_failed")
                self.logger.warning("IpcDealerClient [%s] fire pipe error: %s", self.identity, e)

    # ---------------------------------------------------------
    # Outbound: request-response
    # ---------------------------------------------------------
    def send(
        self,
        dest_identity: str,
        topic: str,
        data: dict,
        timeout: float = 2.0,
    ) -> dict:
        """
        Send a command and block until a reply arrives or timeout elapses.

        Safe to call from any thread *except* the loop thread (deadlock).
        Only one send() may be in-flight at a time.

        Args:
            dest_identity: ZMQ identity of the target DEALER.
            topic: Command topic string.
            data: Payload dict (JSON-serialisable).
            timeout: Seconds to wait for a reply (default 2.0).

        Returns:
            Reply dict from the remote handler, or an error dict on timeout/failure.
        """
        if self._loop_thread_id is not None and threading.get_ident() == self._loop_thread_id:
            raise RuntimeError(
                "IpcDealerClient.send() called from the loop thread; this will deadlock. "
                "Use fire() or call send() from a different thread."
            )

        payload = orjson.dumps(data)

        with self._send_lock:
            self._reply_event.clear()
            self._reply_slot = None

            with self._pipe_lock:
                try:
                    self._pipe_write.send_multipart(
                        [_CMD_SEND, dest_identity.encode(), topic.encode(), payload],
                        flags=zmq.NOBLOCK,
                    )
                except zmq.ZMQError as e:
                    self.stats.track_event("__ERROR__", "send_pipe_failed")
                    return {"status": "error", "reason": str(e)}

            signalled = self._reply_event.wait(timeout=timeout)
            if not signalled:
                self.stats.track_event("__ERROR__", "reply_timeout")
                return {"status": "error", "reason": "ack timeout"}

            reply = self._reply_slot
            self._reply_slot = None

        return reply if reply is not None else {"status": "error", "reason": "empty reply"}

    # ---------------------------------------------------------
    # Main receive loop — pipe and socket helpers
    # ---------------------------------------------------------
    def _handle_pipe_event(self, events: dict, awaiting_reply: bool) -> bool:
        """Drain one command from the inproc pipe. Returns updated awaiting_reply."""
        if self._pipe_read not in events:
            return awaiting_reply

        try:
            pipe_frames = self._pipe_read.recv_multipart(flags=zmq.NOBLOCK)
        except zmq.Again:
            return awaiting_reply
        except zmq.ZMQError as e:
            self.stats.track_event("__ERROR__", "pipe_recv_failed")
            self.logger.warning("IpcDealerClient [%s] pipe recv error: %s", self.identity, e)
            return awaiting_reply

        if not pipe_frames:
            return awaiting_reply

        cmd = pipe_frames[0]

        if cmd == _CMD_STOP:
            self._running = False
            return awaiting_reply

        if cmd == _CMD_FIRE and len(pipe_frames) == 4:
            _, dest, topic_b, payload_b = pipe_frames  # pylint: disable=unbalanced-tuple-unpacking
            self._send_fire(dest, topic_b, payload_b)
            return awaiting_reply

        if cmd == _CMD_SEND and len(pipe_frames) == 4:
            _, dest, topic_b, payload_b = pipe_frames  # pylint: disable=unbalanced-tuple-unpacking
            return self._send_request(dest, topic_b, payload_b)

        return awaiting_reply

    def _send_fire(self, dest: bytes, topic_b: bytes, payload_b: bytes) -> None:
        try:
            self.socket.send_multipart(
                [dest, _NO_REPLY, topic_b, payload_b],
                flags=zmq.NOBLOCK,
            )
            self.stats.track_packet(
                "__FIRE__",
                topic_b.decode("utf-8", errors="replace"),
                len(dest) + len(topic_b) + len(payload_b),
            )
        except zmq.ZMQError as e:
            self.stats.track_event("__ERROR__", "fire_send_failed")
            self.logger.warning("IpcDealerClient [%s] fire send error: %s", self.identity, e)

    def _send_request(self, dest: bytes, topic_b: bytes, payload_b: bytes) -> bool:
        """Send a request frame. Returns True if now awaiting a reply, False on error."""
        try:
            self.socket.send_multipart(
                [dest, _REPLY_REQUIRED, topic_b, payload_b],
                flags=zmq.NOBLOCK,
            )
            self.stats.track_packet(
                "__OUTGOING__",
                topic_b.decode("utf-8", errors="replace"),
                len(dest) + len(topic_b) + len(payload_b),
            )
            return True
        except zmq.ZMQError as e:
            self.stats.track_event("__ERROR__", "send_failed")
            self.logger.warning("IpcDealerClient [%s] send error: %s", self.identity, e)
            self._reply_slot = {"status": "error", "reason": str(e)}
            self._reply_event.set()
            return False

    def _handle_dealer_frames(self, frames: list, awaiting_reply: bool) -> bool:
        """Process frames received from the DEALER socket. Returns updated awaiting_reply."""
        if len(frames) == 2 and awaiting_reply:
            awaiting_reply = False
            try:
                reply = orjson.loads(frames[-1])
            except (ValueError, TypeError):
                reply = {"status": "error", "reason": "invalid reply payload"}
            self.stats.track_event("__REPLY__", reply.get("status", "data"))
            self._reply_slot = reply
            self._reply_event.set()
            return awaiting_reply

        if len(frames) < 4:
            self.stats.track_event("__DROP__", "short_frame")
            return awaiting_reply

        sender_id, reply_flag, topic_bytes, payload_bytes = (
            frames[0], frames[1], frames[2], frames[3]
        )
        self._dispatch_inbound(sender_id, reply_flag, topic_bytes, payload_bytes)
        return awaiting_reply

    def _dispatch_inbound(
        self,
        sender_id: bytes,
        reply_flag: bytes,
        topic_bytes: bytes,
        payload_bytes: bytes,
    ) -> None:
        wants_reply = (reply_flag == _REPLY_REQUIRED)
        topic = topic_bytes.decode("utf-8", errors="replace")
        total_size = len(sender_id) + len(topic_bytes) + len(payload_bytes)
        self.stats.track_packet("__INCOMING__", topic, total_size)

        try:
            data = orjson.loads(payload_bytes)
        except (ValueError, TypeError):
            self.stats.track_event("__DROP__", "invalid_json")
            if wants_reply:
                self._send_reply(sender_id, {"status": "error", "reason": "invalid payload"})
            return

        handler = self._routes.get(topic)
        if handler is None:
            self.stats.track_event("__DROP__", f"unrouted_{topic}")
            if wants_reply:
                self._send_reply(sender_id, {"status": "error", "reason": f"unknown topic: {topic}"})
            return

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

    # ---------------------------------------------------------
    # Main receive loop
    # ---------------------------------------------------------
    def start(self) -> None:
        """Blocking receive loop. Call in a daemon thread."""
        self._running = True
        self._loop_thread_id = threading.get_ident()

        poller = self._rebuild_poller()
        awaiting_reply = False

        while self._running:
            try:
                events = dict(poller.poll(100))
            except zmq.ZMQError:
                if not self._running:
                    break
                self.stats.track_event("__ERROR__", "poll_failed")
                self._create_and_connect()
                poller = self._rebuild_poller()
                continue

            awaiting_reply = self._handle_pipe_event(events, awaiting_reply)
            if not self._running:
                break

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
                poller = self._rebuild_poller()
                if awaiting_reply:
                    awaiting_reply = False
                    self._reply_slot = {"status": "error", "reason": "socket reconnected"}
                    self._reply_event.set()
                continue

            awaiting_reply = self._handle_dealer_frames(frames, awaiting_reply)

        # ---- loop exit cleanup ----
        self._loop_thread_id = None
        try:
            poller.unregister(self.socket)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            poller.unregister(self._pipe_read)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            self.socket.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            self._pipe_read.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            self._pipe_write.close(linger=0)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            self._ctx.term()
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
        # Wake the loop immediately via the pipe so it doesn't wait for the 100ms poll.
        with self._pipe_lock:
            try:
                self._pipe_write.send_multipart([_CMD_STOP], flags=zmq.NOBLOCK)
            except zmq.ZMQError:
                pass

    def get_stats(self) -> dict:
        return self.stats.get_stats()
