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
from typing import Optional

import zmq

from lib.error_status import PngXpubPortInUseError, PngXsubPortInUseError

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcPubSubBroker:
    """
    XPUB/XSUB broker that:
    - Binds sockets in __init__
    - Runs a blocking proxy loop
    - Lifecycle is fully owned by the process manager
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        xsub_port: int = 0,
        xpub_port: int = 0,
        logger: Optional[logging.Logger] = None,
        name: Optional[str] = "IpcPubSubBroker",
    ):
        self.host = host
        self.name = name
        if logger is None:
            logger = logging.getLogger(f"{__name__}")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

        self.ctx = zmq.Context()

        self.xsub: zmq.Socket = self.ctx.socket(zmq.XSUB)
        self.xsub.setsockopt(zmq.LINGER, 0)

        self.xpub: zmq.Socket = self.ctx.socket(zmq.XPUB)
        self.xpub.setsockopt(zmq.LINGER, 0)
        self.xpub.setsockopt(zmq.XPUB_VERBOSE, 1)

        try:
            self.xsub.bind(f"tcp://{self.host}:{xsub_port}")
        except zmq.ZMQError as e:
            self.xsub.close(linger=0)
            self.ctx.term()
            if e.errno == zmq.EADDRINUSE:
                raise PngXsubPortInUseError(f"{self.name}: XSUB port already in use ({xsub_port})") from e
            raise

        try:
            self.xpub.bind(f"tcp://{self.host}:{xpub_port}")
        except zmq.ZMQError as e:
            self.xsub.close(linger=0)
            self.xpub.close(linger=0)
            self.ctx.term()
            if e.errno == zmq.EADDRINUSE:
                raise PngXpubPortInUseError(f"{self.name}: XPUB port already in use ({xpub_port})") from e
            raise

        self.xsub_port = int(
            self.xsub.getsockopt(zmq.LAST_ENDPOINT).split(b":")[-1]
        )
        self.xpub_port = int(
            self.xpub.getsockopt(zmq.LAST_ENDPOINT).split(b":")[-1]
        )
        self.control = self.ctx.socket(zmq.PAIR)
        self.control.setsockopt(zmq.LINGER, 0)
        self.control.bind(f"inproc://{self.name}-control")

        self._control_client = self.ctx.socket(zmq.PAIR)
        self._control_client.setsockopt(zmq.LINGER, 0)
        self._control_client.connect(f"inproc://{self.name}-control")


        self.logger.debug(
            f"{self.name} bound: "
            f"XSUB=tcp://{self.host}:{self.xsub_port}, "
            f"XPUB=tcp://{self.host}:{self.xpub_port}"
        )

        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self):
        """
        Blocking broker loop.
        This should be run in its own process OR thread.
        """
        self.logger.debug(
            f"{self.name} running: "
            f"XSUB={self.xsub_port}, XPUB={self.xpub_port}"
        )

        try:
            zmq.proxy_steerable(
                self.xsub,
                self.xpub,
                None,
                self._control_client
            )
        except zmq.ZMQError as e:
            self.logger.debug("Broker proxy exited: %s", e)
        finally:
            self.logger.debug("Broker proxy loop exited")

    def run_in_thread(self, name: str = "IPC-Broker") -> threading.Thread:
        """
        Runs the broker in a background daemon thread.
        """
        if self._thread and self._thread.is_alive():
            return self._thread

        self._thread = threading.Thread(
            target=self.run,
            daemon=True,
            name=name,
        )
        self._thread.start()
        return self._thread

    def close(self):
        try:
            self.control.send(b"TERMINATE")
        except Exception:
            pass

        if self._thread:
            self._thread.join(timeout=0.2)

        for sock in (self.xsub, self.xpub, self.control, self._control_client):
            try:
                sock.close(linger=0)
            except Exception:
                pass

        try:
            self.ctx.term()
        except Exception:
            pass

        self.logger.debug("%s closed", self.name)
