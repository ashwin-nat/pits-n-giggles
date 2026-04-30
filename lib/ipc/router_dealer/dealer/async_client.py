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

import asyncio
import logging
from typing import Callable, Dict, Optional

import orjson
import zmq
import zmq.asyncio

from lib.event_counter import EventCounter

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_REPLY_REQUIRED = b"\x01"
_NO_REPLY       = b"\x00"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class _ReplyCoordinator:
    """Encapsulates the one-in-flight reply future for IpcDealerAsync."""

    def __init__(self) -> None:
        self._future: Optional[asyncio.Future] = None

    def new_waiter(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._future = fut
        return fut

    def deliver(self, frames: list) -> bool:
        if self._future is not None and not self._future.done():
            self._future.set_result(frames)
            return True
        return False

    def cancel(self, exc: Exception) -> None:
        if self._future is not None and not self._future.done():
            self._future.set_exception(exc)


class IpcDealerAsync:
    """
    Async ZeroMQ DEALER client — bidirectional.

    Connects to an IpcRouter with a fixed ZMQ identity. ZMQ handles TCP
    reconnection internally — no reconnect loop is needed.

    Outbound modes:

    **Fire-and-forget** — send and return immediately::

        await dealer.fire("hud", "hud-toggle-notification", {"oid": "mfd"})

    **Request-response** — send and await reply::

        stats = await dealer.send("hud", "get-stats", {})

    Inbound (optional): register handlers via ``route(topic)`` and call
    ``await dealer.start()`` to spawn the background receive loop. Inbound
    frames arrive as ``[sender_id, reply_flag, topic, payload]``; replies to
    a prior outbound ``send()`` arrive as ``[sender_id, reply_payload]`` and
    are demuxed by frame count.

    Notes:
      - Only one outbound ``send()`` may be in-flight at a time (protocol has
        no correlation ID). Enforced by an internal lock.
      - Async handlers should be ``async def``; sync handlers must be fast —
        anything that blocks stalls the recv loop.

    Usage::

        dealer = IpcDealerAsync(port=53836, identity="backend")

        @dealer.route("ping")
        async def on_ping(data: dict) -> dict:
            return {"status": "ok", "echo": data}

        await dealer.start()  # only needed if you registered routes

        await dealer.fire("hud", "hud-toggle-notification", {"oid": "mfd"})
        stats = await dealer.send("hud", "get-stats", {})

        await dealer.close()
    """

    ACK_TIMEOUT = 2.0  # seconds to wait for a reply before giving up

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
            logger = logging.getLogger(f"{__name__}.IpcDealerAsync")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self._ctx = zmq.asyncio.Context()
        self.socket: Optional[zmq.asyncio.Socket] = None
        self._send_lock = asyncio.Lock()
        self.stats = EventCounter()

        self._routes: Dict[str, Callable[[dict], object]] = {}
        self._replies = _ReplyCoordinator()
        self._recv_task: Optional[asyncio.Task] = None

        self._connect()

    # ---------------------------------------------------------
    # Socket setup — ZMQ handles reconnection internally
    # ---------------------------------------------------------
    def _connect(self) -> None:
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
        self.logger.debug("IpcDealerAsync [%s] connected to %s", self.identity, endpoint)

    # ---------------------------------------------------------
    # Recv loop lifecycle
    # ---------------------------------------------------------
    def _ensure_recv_loop(self) -> None:
        if self._recv_task is None or self._recv_task.done():
            self._recv_task = asyncio.create_task(self._recv_loop())

    # ---------------------------------------------------------
    # Inbound routing
    # ---------------------------------------------------------
    def route(self, topic: str):
        """Decorator to register a handler for a topic string."""
        def decorator(func: Callable[[dict], object]):
            self._routes[topic] = func
            return func
        return decorator

    async def start(self) -> None:
        """
        Spawn the background receive loop. Required only if inbound routing
        is needed (i.e. handlers were registered via ``route()``).

        Idempotent: calling twice has no effect.
        """
        self._ensure_recv_loop()

    async def _recv_loop(self) -> None:
        """
        Single reader for the DEALER socket. Demuxes by frame count:
          - 2 frames → reply to a pending outbound send()
          - 4 frames → unsolicited inbound command → dispatch to handler
        """
        try:
            while True:
                try:
                    frames = await self.socket.recv_multipart()
                except zmq.ZMQError as e:
                    self.stats.track_event("__ERROR__", "recv_failed")
                    self.logger.warning(
                        "IpcDealerAsync [%s] recv error: %s", self.identity, e
                    )
                    continue

                if len(frames) == 2:
                    # Reply to a pending send()
                    if not self._replies.deliver(frames):
                        self.stats.track_event("__DROP__", "unexpected_reply")
                    continue

                if len(frames) >= 4:
                    await self._handle_inbound(frames)
                    continue

                self.stats.track_event("__DROP__", "short_frame")
        except asyncio.CancelledError:
            return

    async def _handle_inbound(self, frames: list) -> None:
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
                await self._send_reply(sender_id, {"status": "error", "reason": "invalid payload"})
            return

        handler = self._routes.get(topic)
        if handler is None:
            self.stats.track_event("__DROP__", f"unrouted_{topic}")
            if wants_reply:
                await self._send_reply(sender_id, {"status": "error", "reason": f"unknown topic: {topic}"})
            return

        try:
            result = handler(data)
            if asyncio.iscoroutine(result):
                result = await result
            self.stats.track_event("__HANDLER_OK__", topic)
            if wants_reply:
                reply = result if isinstance(result, dict) else {"status": "ok"}
                await self._send_reply(sender_id, reply)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.stats.track_event("__HANDLER_ERR__", topic)
            self.logger.exception("Handler error for topic %r: %s", topic, e)
            if wants_reply:
                await self._send_reply(sender_id, {"status": "error", "reason": str(e)})

    async def _send_reply(self, sender_id: bytes, reply: dict) -> None:
        try:
            await self.socket.send_multipart([sender_id, orjson.dumps(reply)])
            self.stats.track_event("__REPLY__", reply.get("status", "data"))
        except zmq.ZMQError as e:
            self.stats.track_event("__ERROR__", "reply_send_failed")
            self.logger.warning("IpcDealerAsync [%s] failed to send reply: %s", self.identity, e)

    # ---------------------------------------------------------
    # Fire-and-forget
    # ---------------------------------------------------------
    async def fire(self, dest_identity: str, topic: str, data: dict) -> None:
        """
        Send a command and return immediately — no reply is awaited.

        Use for high-frequency or best-effort commands where the sender does not
        need confirmation that the recipient processed the message.

        Args:
            dest_identity: ZMQ identity of the target DEALER (e.g. ``"hud"``).
            topic: Command topic string.
            data: Payload dict (JSON-serialisable).
        """
        payload = orjson.dumps(data)
        total_size = len(dest_identity) + len(topic) + len(payload)

        try:
            await self.socket.send_multipart(
                [dest_identity.encode(), _NO_REPLY, topic.encode(), payload]
            )
            self.stats.track_packet("__FIRE__", topic, total_size)
        except zmq.ZMQError as e:
            self.stats.track_event("__ERROR__", "fire_failed")
            self.logger.warning(
                "IpcDealerAsync [%s] fire error to %r: %s", self.identity, dest_identity, e
            )

    # ---------------------------------------------------------
    # Request-response (awaits reply)
    # ---------------------------------------------------------
    async def send(self, dest_identity: str, topic: str, data: dict) -> dict:
        """
        Send a command and await a reply from the recipient.

        Args:
            dest_identity: ZMQ identity of the target DEALER (e.g. ``"hud"``).
            topic: Command topic string.
            data: Payload dict (JSON-serialisable).

        Returns:
            Reply dict from the handler, e.g. ``{"status": "ok"}`` or rich data.
            Returns an error dict without raising on timeout or send failure.
        """
        payload = orjson.dumps(data)
        total_size = len(dest_identity) + len(topic) + len(payload)

        async with self._send_lock:
            self._ensure_recv_loop()
            future = self._replies.new_waiter()

            try:
                try:
                    await self.socket.send_multipart(
                        [dest_identity.encode(), _REPLY_REQUIRED, topic.encode(), payload]
                    )
                    self.stats.track_packet("__OUTGOING__", topic, total_size)
                except zmq.ZMQError as e:
                    self.stats.track_event("__ERROR__", "send_failed")
                    self.logger.warning(
                        "IpcDealerAsync [%s] send error to %r: %s", self.identity, dest_identity, e
                    )
                    return {"status": "error", "reason": str(e)}

                try:
                    frames = await asyncio.wait_for(future, timeout=self.ACK_TIMEOUT)
                except asyncio.TimeoutError:
                    self.stats.track_event("__ERROR__", "reply_timeout")
                    self.logger.warning(
                        "IpcDealerAsync [%s] reply timeout for topic %r to %r",
                        self.identity, topic, dest_identity,
                    )
                    return {"status": "error", "reason": "ack timeout"}
                except asyncio.CancelledError:
                    return {"status": "error", "reason": "cancelled"}
            finally:
                self._replies.cancel(Exception("send completed"))

        if not frames:
            return {"status": "error", "reason": "empty reply"}

        try:
            reply = orjson.loads(frames[-1])
            self.stats.track_event("__REPLY__", reply.get("status", "data"))
            return reply
        except (ValueError, TypeError):
            self.stats.track_event("__ERROR__", "invalid_reply")
            return {"status": "error", "reason": "invalid reply payload"}

    # ---------------------------------------------------------
    # Shutdown / stats
    # ---------------------------------------------------------
    async def close(self) -> None:
        self._replies.cancel(asyncio.CancelledError("dealer closed"))

        if self._recv_task is not None:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except (asyncio.CancelledError, Exception):  # pylint: disable=broad-exception-caught
                pass
            self._recv_task = None

        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        try:
            self._ctx.term()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self.logger.debug("IpcDealerAsync [%s] closed", self.identity)

    def get_stats(self) -> dict:
        return self.stats.get_stats()
