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
from typing import Optional

import orjson
import zmq
import zmq.asyncio

from lib.event_counter import EventCounter

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_REPLY_REQUIRED = b"\x01"
_NO_REPLY       = b"\x00"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcDealerAsync:
    """
    Async ZeroMQ DEALER client for sending routed commands.

    Connects to an IpcRouter with a fixed ZMQ identity. ZMQ handles TCP
    reconnection internally — no reconnect loop is needed.

    Supports two modes:

    **Fire-and-forget** — send and return immediately::

        await dealer.fire("hud", "hud-toggle-notification", {"oid": "mfd"})

    **Request-response** — send and await reply::

        stats = await dealer.send("hud", "get-stats", {})

    Usage::

        dealer = IpcDealerAsync(port=53836, identity="backend")

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
                frames = await asyncio.wait_for(
                    self.socket.recv_multipart(),
                    timeout=self.ACK_TIMEOUT,
                )
            except asyncio.TimeoutError:
                self.stats.track_event("__ERROR__", "reply_timeout")
                self.logger.warning(
                    "IpcDealerAsync [%s] reply timeout for topic %r to %r",
                    self.identity, topic, dest_identity,
                )
                return {"status": "error", "reason": "ack timeout"}
            except zmq.ZMQError as e:
                self.stats.track_event("__ERROR__", "recv_failed")
                return {"status": "error", "reason": str(e)}

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
        if self.socket:
            try:
                self.socket.close(linger=0)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        self.logger.debug("IpcDealerAsync [%s] closed", self.identity)

    def get_stats(self) -> dict:
        return self.stats.get_stats()
