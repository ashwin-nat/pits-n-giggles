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

    BUILTIN_COMMANDS = {"__terminate__", "__heartbeat__", "__shutdown__", "__ping__"}

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
        self._serve_thread_id: Optional[int] = None
        self._running = False
        self._shutdown_callback: Optional[Callable[[dict], dict]] = None
        self._command_handlers: dict[str, Callable[[dict], dict]] = {}
        self._register_builtin_handlers()

        # Heartbeat parameters
        self.max_missed_heartbeats = max_missed_heartbeats
        self.heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat = None
        self._missed_heartbeats = 0
        self._heartbeat_missed_callback: Optional[Callable[[int], None]] = None
        self._heartbeat_thread: Optional[threading.Thread] = None

        if logger is None:
            logger = logging.getLogger(f"{__name__}")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.logger = logger

    # -------------------------------------- DECORATORS -----------------------------------------------------------------

    def _register_builtin_handlers(self) -> None:
        """Registers builtin command handlers."""
        self._command_handlers["__terminate__"] = self._handle_terminate
        self._command_handlers["__heartbeat__"] = self._handle_heartbeat
        self._command_handlers["__shutdown__"] = self._handle_shutdown
        self._command_handlers["__ping__"] = self._handle_ping

    def on_command(self, cmd_name: str) -> Callable[[Callable[[dict], dict]], Callable[[dict], dict]]:
        """Registers a handler for a non-builtin command using decorator syntax."""
        if cmd_name in self.BUILTIN_COMMANDS:
            raise ValueError(f"'{cmd_name}' is a reserved builtin command")

        def decorator(callback: Callable[[dict], dict]) -> Callable[[dict], dict]:
            self._command_handlers[cmd_name] = callback
            return callback

        return decorator

    def on_shutdown(self, callback: Callable[[dict], dict]) -> Callable[[dict], dict]:
        """Registers a shutdown callback using decorator syntax."""
        self._shutdown_callback = callback
        return callback

    def on_heartbeats_missed(self, callback: Callable[[int], None]) -> Callable[[int], None]:
        """Registers a heartbeat-missed callback using decorator syntax."""
        self._heartbeat_missed_callback = callback
        return callback

    # -------------------------------------- HEARTBEAT ------------------------------------------------------------------

    def _def_heartbeat_missed_callback(self, _missed_heartbeats: int) -> None:
        """Default heartbeat missed callback. no-op"""
        return

    def _handle_terminate(self, _args: dict) -> dict:
        """Handles force termination."""
        self._running = False
        return {"status": "success", "message": "terminated", "source": self.name}

    def _handle_heartbeat(self, _args: dict) -> dict:
        """Handles incoming heartbeat and resets missed counter."""
        self._last_heartbeat = time.time()
        self._missed_heartbeats = 0
        return {"status": "success", "reply": "__heartbeat_ack__", "source": self.name}

    def _handle_shutdown(self, args: dict) -> dict:
        """Handles graceful shutdown."""
        if self._shutdown_callback:
            response = self._shutdown_callback(args)
        else:
            response = {
                "status": "success",
                "message": "default shutdown complete",
            }
        self._running = False
        return response

    def _handle_ping(self, _args: dict) -> dict:
        """Handles ping command."""
        return {"reply": "__pong__", "source": self.name}

    def _dispatch_command(self, msg: dict) -> dict:
        """Routes a command to builtin handlers or user-registered handlers."""
        cmd = msg.get("cmd")
        args = msg.get("args", {})

        handler = self._command_handlers.get(cmd)
        if handler is None:
            return {"status": "error", "message": f"unknown command: {cmd}", "source": self.name}

        return handler(args)

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

    def serve(self, timeout: Optional[float] = None) -> None:
        """
        Starts the request loop. Routes incoming requests to command handlers.
        :param timeout: Optional timeout (in seconds) for recv_json.
                        Ensures loop remains responsive even with no messages.
        """
        self._serve_thread_id = threading.get_ident()
        self._running = True

        # Start heartbeat monitor only if callback is registered
        if self._heartbeat_missed_callback is not None:
            self._last_heartbeat = time.time()
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True,
                                                      name=f"{self.name} heartbeat monitor")
            self._heartbeat_thread.start()

        poller = zmq.Poller()
        poller.register(self.sock, zmq.POLLIN)

        try:
            while self._running:
                # pylint: disable=too-many-try-statements
                try:
                    socks = dict(poller.poll(timeout * 1000 if timeout else None))
                    if self.sock not in socks:
                        # No message received within timeout; continue loop
                        continue

                    msg = self.sock.recv_json()
                    response = self._dispatch_command(msg)
                    self.sock.send_json(response)

                except Exception as e:  # pylint: disable=broad-except
                    self.logger.exception("%s: Error in serve loop: error: %s", self.name, e)
                    if self._running:
                        self.sock.send_json({"error": str(e)})
        finally:
            try:
                self.close()
            finally:
                self._serve_thread_id = None

    def serve_in_thread(self, timeout: Optional[float] = None, name: Optional[str] = None) -> threading.Thread:
        """Starts the serve loop in a background thread.

        Args:
            timeout (Optional[float]): Optional timeout (in seconds) for recv_json.
                                       Ensures loop remains responsive even with no messages.
            name (Optional[str]): Optional name for the thread.

        Returns:
            threading.Thread: The thread handle.
        """
        tname = name or f"IPC listener for {self.name}"
        self._thread = threading.Thread(target=self.serve, args=(timeout,), daemon=True, name=tname)
        self._thread.start()
        return self._thread

    def close(self) -> None:
        """Closes the socket and stops all threads cleanly."""
        self._running = False
        self.logger.debug("%s closing", self.name)

        # If serve loop is running in another thread, let it perform final ZMQ teardown.
        if self._serve_thread_id is not None and threading.get_ident() != self._serve_thread_id:
            return

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
