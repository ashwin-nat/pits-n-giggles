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
import threading
import time
from typing import Optional

import zmq

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcPubSubBroker:
    """
    XPUB/XSUB broker that:
    - Auto-prepares (binds) in __init__
    - Runs proxy loop in background thread
    - Auto-restarts on crash (re-prepare + proxy)
    - Keeps ports stable and discoverable immediately
    """

    RESTART_DELAY = 0.1

    def __init__(self, host="127.0.0.1", xsub_port=0, xpub_port=0, logger=None):
        self.host = host
        self.logger = logger or logging.getLogger("ipc-broker")

        self.ctx = zmq.Context()

        self._configured_xsub_port = xsub_port
        self._configured_xpub_port = xpub_port

        self.xsub: Optional[zmq.Socket] = None
        self.xpub: Optional[zmq.Socket] = None

        self.xsub_port: Optional[int] = None
        self.xpub_port: Optional[int] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._prepare()
        self.logger.debug(
            f"ZmqBroker prepared: "
            f"XSUB={self.xsub_endpoint}, XPUB={self.xpub_endpoint}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Starts the broker supervisor thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._supervisor_loop,
            daemon=True,
            name="IPC-Broker",
        )
        self._thread.start()

        self.logger.debug("ZmqBroker supervisor started")

    def close(self):
        """Stops broker and shuts down sockets."""
        self._running = False
        self._cleanup_sockets()
        self.logger.debug("ZmqBroker closed")

    @property
    def xpub_endpoint(self) -> str:
        return f"tcp://{self.host}:{self.xpub_port}"

    @property
    def xsub_endpoint(self) -> str:
        return f"tcp://{self.host}:{self.xsub_port}"

    @property
    def running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Supervisor loop
    # ------------------------------------------------------------------

    def _supervisor_loop(self):
        while self._running:
            try:
                self.logger.debug(
                    f"ZmqBroker active: "
                    f"XSUB={self.xsub_port}, XPUB={self.xpub_port}"
                )

                # Blocking until crash or close()
                zmq.proxy(self.xsub, self.xpub)

            except Exception as e:
                if not self._running:
                    break
                self.logger.error(f"ZmqBroker proxy crashed: {e}")

            finally:
                self._cleanup_sockets()

                if self._running:
                    time.sleep(self.RESTART_DELAY)
                    self._prepare()   # 🔁 re-bind + re-discover ports

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare(self):
        """Bind XPUB/XSUB sockets and discover ports."""
        if self.xsub or self.xpub:
            return

        self.xsub = self.ctx.socket(zmq.XSUB)
        self.xsub.setsockopt(zmq.LINGER, 0)

        self.xpub = self.ctx.socket(zmq.XPUB)
        self.xpub.setsockopt(zmq.LINGER, 0)
        self.xpub.setsockopt(zmq.XPUB_VERBOSE, 1)

        self.xsub.bind(f"tcp://{self.host}:{self._configured_xsub_port}")
        self.xpub.bind(f"tcp://{self.host}:{self._configured_xpub_port}")

        self.xsub_port = int(
            self.xsub.getsockopt(zmq.LAST_ENDPOINT).split(b":")[-1]
        )
        self.xpub_port = int(
            self.xpub.getsockopt(zmq.LAST_ENDPOINT).split(b":")[-1]
        )

    def _cleanup_sockets(self):
        if self.xsub:
            try:
                self.xsub.close(linger=0)
            except Exception:
                pass
            self.xsub = None

        if self.xpub:
            try:
                self.xpub.close(linger=0)
            except Exception:
                pass
            self.xpub = None
