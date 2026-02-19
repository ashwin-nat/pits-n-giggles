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

import threading
import time
import logging
from typing import Callable, Optional

import zmq

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcServerSync:
    """
    Synchronous ZeroMQ REP socket server.
    Used by child process to handle requests synchronously.
    Can be run in a dedicated thread.
    Includes optional heartbeat monitoring (only active if callback registered).
    """

    def __init__(self, port: int | None = None, name: str = "IpcChildSync",
                max_missed_heartbeats: int = 3, heartbeat_timeout: float = 5.0,
                logger: Optional[logging.Logger] = None):
        """
        :param port: Port to bind to. If None, OS chooses a free port.
        :param name: Name of the child process.
        :param max_missed_heartbeats: Number of consecutive missed heartbeats before calling callback.
        :param heartbeat_timeout: Time in seconds to wait for heartbeat before considering it missed.
        :param logger: Logger to use. If None, a NullHandler is used.
        """
        self.name = name
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.REP)

        if port is None:
            # Bind to a free port chosen by OS
            self.sock.bind("tcp://127.0.0.1:*")
            endpoint = self.sock.getsockopt(zmq.LAST_ENDPOINT).decode()
            self.endpoint = endpoint
            self.port = int(endpoint.rsplit(":", 1)[1])
        else:
            self.endpoint = f"tcp://127.0.0.1:{port}"
            self.port = port
            self.sock.bind(self.endpoint)

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._shutdown_callback = None

        # Heartbeat parameters
        self.max_missed_heartbeats = max_missed_heartbeats
        self.heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat = None
        self._missed_heartbeats = 0
        self._heartbeat_missed_callback = None
        self._heartbeat_thread: Optional[threading.Thread] = None

        if logger is None:
            logger = logging.getLogger(f"{__name__}")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

    # -------------------------------------- CALLBACKS ------------------------------------------------------------------

    def register_shutdown_callback(self, callback: Callable[[dict], dict]) -> None:
        """
        Registers a callback to be called on shutdown command.
        :param callback: Function to call on shutdown command.
        """
        self._shutdown_callback = callback

    def register_heartbeat_missed_callback(self, callback: Callable[[int], None]) -> None:
        """
        Registers a callback to be called when max consecutive heartbeats are missed.
        Callback receives the number of missed heartbeats.
        Registering this callback automatically enables heartbeat monitoring.
        """
        self._heartbeat_missed_callback = callback

    # -------------------------------------- HEARTBEAT ------------------------------------------------------------------

    def _def_heartbeat_missed_callback(self, _missed_heartbeats: int) -> None:
        """Default heartbeat missed callback. no-op"""
        return

    def _handle_heartbeat(self) -> dict:
        """Handles incoming heartbeat and resets missed counter."""
        self._last_heartbeat = time.time()
        self._missed_heartbeats = 0
        return {"status": "success", "reply": "__heartbeat_ack__", "source": self.name}

    def _heartbeat_monitor(self) -> None:
        """Runs in a background thread to monitor heartbeats."""
        while self._running:
            time.sleep(self.heartbeat_timeout)
            if not self._running:
                break

            # Skip until first heartbeat received
            if self._last_heartbeat is None:
                continue

            elapsed = time.time() - self._last_heartbeat
            if elapsed > self.heartbeat_timeout:
                self._missed_heartbeats += 1
                self.logger.debug("%s: Missed heartbeat. count: %d", self.name, self._missed_heartbeats)
                if self._missed_heartbeats >= self.max_missed_heartbeats:
                    try:
                        callback = self._heartbeat_missed_callback or self._def_heartbeat_missed_callback
                        callback(self._missed_heartbeats)
                        break
                    except Exception:  # pylint: disable=broad-except
                        break

    # -------------------------------------- MAIN LOOP ------------------------------------------------------------------

    def serve(self, handler_fn: Callable[[dict], dict], timeout: Optional[float] = None) -> None:
        """
        Starts the request loop. Calls handler_fn on each request.
        :param handler_fn: Function to handle each request.
        :param timeout: Optional timeout (in seconds) for recv_json.
                        Ensures loop remains responsive even with no messages.
        """
        self._running = True

        # Start heartbeat monitor only if callback is registered
        if self._heartbeat_missed_callback is not None:
            self._last_heartbeat = time.time()
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True,
                                                      name=f"{self.name} heartbeat monitor")
            self._heartbeat_thread.start()

        poller = zmq.Poller()
        poller.register(self.sock, zmq.POLLIN)

        while self._running:
            # pylint: disable=too-many-try-statements
            try:
                socks = dict(poller.poll(timeout * 1000 if timeout else None))
                if self.sock not in socks:
                    # No message received within timeout; continue loop
                    continue

                msg = self.sock.recv_json()
                cmd = msg.get("cmd")

                if cmd == "__terminate__":
                    self._running = False
                    break

                if cmd == "__heartbeat__":
                    response = self._handle_heartbeat()
                    self.sock.send_json(response)
                    continue

                if cmd == "__ping__":
                    response = {"reply": "__pong__", "source": self.name}
                    self.sock.send_json(response)
                    continue

                if cmd == "__shutdown__":
                    if self._shutdown_callback:
                        response = self._shutdown_callback(msg.get("args", {}))
                    else:
                        response = {
                            "status": "success",
                            "message": "default shutdown complete",
                        }
                    self._running = False
                else:
                    response = handler_fn(msg)

                self.sock.send_json(response)

            except Exception as e:  # pylint: disable=broad-except
                self.logger.exception("%s: Error in serve loop: cmd: %s error: %s", self.name, cmd, e)
                if self._running:
                    self.sock.send_json({"error": str(e)})

        self.close()

    def serve_in_thread(self, handler_fn: Callable[[dict], dict], timeout: Optional[float] = None, name: Optional[str] = None) -> threading.Thread:
        """Starts the serve loop in a background thread.

        Args:
            handler_fn (Callable[[dict], dict]): Function to handle each request.
            timeout (Optional[float]): Optional timeout (in seconds) for recv_json.
                                       Ensures loop remains responsive even with no messages.
            name (Optional[str]): Optional name for the thread.

        Returns:
            threading.Thread: The thread handle.
        """
        tname = name or f"IPC listener for {self.name}"
        self._thread = threading.Thread(target=self.serve, args=(handler_fn, timeout), daemon=True, name=tname)
        self._thread.start()
        return self._thread

    def close(self) -> None:
        """Closes the socket and stops all threads cleanly."""
        if not self._running:
            return  # Already closed

        self._running = False
        self.logger.debug("%s closing", self.name)

        # Gracefully stop heartbeat monitor if active
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=self.heartbeat_timeout + 0.5)

        # Give the serve loop a moment to finish its current iteration
        time.sleep(0.05)

        try:
            # Use linger 0 to discard pending messages immediately
            self.sock.setsockopt(zmq.LINGER, 0)
            self.sock.close()
        except Exception: # pylint: disable=broad-except
            pass

        try:
            self.ctx.term()
        except Exception: # pylint: disable=broad-except
            pass
