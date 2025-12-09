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

import json
import logging
from typing import Any, Callable, Dict, Optional

from ._contracts import ReaderTransport, WriterTransport
from .transport import ShmTransportReader, ShmTransportWriter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngShmWriter:
    """
    Presentation-layer writer.

    - Accepts JSON-serializable topic payloads
    - Batches multiple topics into a single frame
    - Uses SHM transport by default
    - Allows full transport override for tests
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        transport: Optional[WriterTransport] = None,
    ):
        """
        :param logger: Optional logger
        :param transport: Optional transport override
        """
        self.logger = logger or logging.getLogger(__name__)

        self._transport: WriterTransport = (
            transport if transport is not None
            else ShmTransportWriter(logger=self.logger)
        )

        self._frame: Dict[str, Any] = {}

    def add(self, topic: str, data: Dict[str, Any]) -> None:
        """
        Add a topic payload to the current frame.

        :param topic: Topic name
        :param data: JSON-serializable payload
        """
        self._frame[topic] = data

    async def write(self) -> None:
        """
        Write the current frame to the transport.
        """

        if not self._frame:
            return

        try:
            payload = json.dumps(
                self._frame,
                separators=(",", ":"),
            ).encode("utf-8")
        except Exception:
            self.logger.exception("Failed to serialize IPC payload")
            self._frame.clear()
            return

        await self._transport.write(payload)
        self._frame.clear()

    def close(self) -> None:
        """
        Close the transport.
        """
        self.logger.debug("Closing PNG SHM writer transport")
        self._transport.close()

class PngShmReader:
    """
    Presentation-layer reader.

    - Uses decorator-based topic handlers
    - Uses SHM transport by default
    - Allows full transport override for tests
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        transport: Optional[ReaderTransport] = None,
        read_interval_ms: int = 33, # ~30 FPS
    ):
        """
        :param logger: Optional logger
        :param transport: Optional transport override
        :param read_interval_ms: Polling interval in milliseconds
        """
        self.logger = logger or logging.getLogger(__name__)
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

        if transport is None:
            self._transport: ReaderTransport = ShmTransportReader(
                read_interval_ms=read_interval_ms,
                on_payload=self.on_payload,
                logger=self.logger,
            )
        else:
            self._transport = transport

    # -------- Decorator API --------

    def on(self, topic: str):
        """
        Decorator for registering topic handlers.
        """
        def decorator(fn: Callable[[Dict[str, Any]], None]):
            self._handlers[topic] = fn
            return fn
        return decorator

    # -------- Transport Callback --------

    def on_payload(self, payload: bytes) -> None:
        """
        Callback for received payloads.
        """
        try:
            frame = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as e:
            self.logger.debug(f"Invalid JSON payload dropped: {e}")
            return
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.exception(f"Invalid JSON payload dropped: {e}")
            return

        if not isinstance(frame, dict):
            return

        for topic, data in frame.items():
            handler = self._handlers.get(topic)
            if not handler:
                continue

            try:
                handler(data)
            except Exception:
                self.logger.exception(
                    f"Handler failed for topic '{topic}'"
                )

    # -------- Public Control --------

    def read(self) -> None:
        """
        Blocking read loop.
        """
        self._transport.run()

    def stop(self) -> None:
        """
        Request a clean shutdown of the run loop.
        """
        self._transport.stop()

    def close(self) -> None:
        """
        Close the transport.
        """
        self._transport.close()
