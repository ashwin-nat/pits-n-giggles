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
from typing import Awaitable, Callable, Optional

from lib.ipc.pubsub.subscriber import IpcSubscriberAsync

from .base_receiver import TelemetryTransport

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcTransport(TelemetryTransport):
    """TelemetryTransport that reads raw F1 binary packets from an IPC pub/sub topic.

    Delivers raw bytes to the registered on_packet callback using the async-native
    IpcSubscriberAsync, keeping all I/O on the event loop without cross-thread plumbing.
    """

    def __init__(self, host: str, port: int, topic: str, logger: Optional[logging.Logger] = None) -> None:
        """
        Args:
            host (str): IPC broker host.
            port (int): IPC broker port.
            topic (str): Topic to subscribe to (must carry raw F1 binary payloads).
            logger (Logger, optional): Logger to use.
        """
        self._topic = topic
        self._logger = logger or logging.getLogger(__name__)
        self._subscriber = IpcSubscriberAsync(host=host, port=port, logger=self._logger)
        self._callback: Optional[Callable[[bytes], Awaitable[None]]] = None

    def on_packet(self, callback: Callable[[bytes], Awaitable[None]]) -> Callable[[bytes], Awaitable[None]]:
        """Decorator to register the packet callback."""
        self._callback = callback
        return callback

    async def run(self) -> None:
        """Run until cancelled, delivering raw packets to the registered callback."""
        if self._callback is None:
            raise RuntimeError(
                "IpcTransport.run() called before a packet callback was registered. "
                "Use `on_packet` to register an async callback before calling `run`."
            )

        callback = self._callback

        @self._subscriber.route_raw(self._topic)
        async def _on_raw(raw: bytes) -> None:
            await callback(raw)

        await self._subscriber.run()

    async def close(self) -> None:
        """Signal the subscriber loop to stop."""
        self._subscriber.close()
