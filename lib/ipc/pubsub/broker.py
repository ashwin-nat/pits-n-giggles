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
import threading
import logging
from typing import Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ZmqBroker:
    """
    ZeroMQ XPUB/XSUB forwarder.

    - Binds XSUB + XPUB sockets.
    - Uses OS-assigned ports if port=None.
    - Exposes xsub_port and xpub_port.
    - Runs proxy in a background thread.
    - Shutdown via close().
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        xsub_port: Optional[int] = None,
        xpub_port: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.host = host
        self.logger = logger
        self._context = zmq.Context.instance()

        # ---- XSUB socket (writers connect here) ----
        self.xsub_sock = self._context.socket(zmq.XSUB)
        self.xsub_sock.setsockopt(zmq.LINGER, 0)

        xsub_addr = f"tcp://{host}:{xsub_port if xsub_port else 0}"
        self.xsub_sock.bind(xsub_addr)
        # Determine actual port (useful when port was None)
        self._xsub_endpoint = self.xsub_sock.getsockopt_string(zmq.LAST_ENDPOINT)
        self.xsub_port = int(self._xsub_endpoint.rsplit(":", 1)[1])

        # ---- XPUB socket (consumers connect here) ----
        self.xpub_sock = self._context.socket(zmq.XPUB)
        self.xpub_sock.setsockopt(zmq.LINGER, 0)
        # NOTE: XPUB must forward subscription messages
        self.xpub_sock.setsockopt(zmq.XPUB_VERBOSE, 1)

        xpub_addr = f"tcp://{host}:{xpub_port if xpub_port else 0}"
        self.xpub_sock.bind(xpub_addr)
        self._xpub_endpoint = self.xpub_sock.getsockopt_string(zmq.LAST_ENDPOINT)
        self.xpub_port = int(self._xpub_endpoint.rsplit(":", 1)[1])

        if self.logger:
            self.logger.info(
                f"ZmqBroker XSUB={self._xsub_endpoint}, XPUB={self._xpub_endpoint}"
            )

        self._running = False
        self._thread = None

    @property
    def xsub_endpoint(self) -> str:
        return self._xsub_endpoint

    @property
    def xpub_endpoint(self) -> str:
        return self._xpub_endpoint

    def start(self):
        if self._running:
            return
        self._running = True

        # The proxy runs forever -> must be thread
        def _proxy():
            try:
                zmq.proxy(self.xsub_sock, self.xpub_sock)
            except zmq.ContextTerminated:
                pass
            except Exception as e:
                if self.logger:
                    self.logger.error(f"ZMQ proxy error: {e}")

        self._thread = threading.Thread(target=_proxy, daemon=True)
        self._thread.start()

        if self.logger:
            self.logger.info("ZmqBroker started")

    def close(self):
        self._running = False
        try:
            self.xsub_sock.close(linger=0)
        except Exception:
            pass
        try:
            self.xpub_sock.close(linger=0)
        except Exception:
            pass

        # Termination of context is optional depending on your architecture
        # But safe since we use instance() and sockets are closed
        try:
            # NO context.term() here if shared across components
            pass
        except Exception:
            pass

        if self.logger:
            self.logger.info("ZmqBroker closed")
