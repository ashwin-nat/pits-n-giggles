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

# TODO: run imports organizer
from typing import Optional, Callable
import logging
import threading
import time

import socketio

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseSubscriber:
    """
    Base class for a synchronous Socket.IO client running in its own thread.
    Subclasses register events via @self.on('event-name') and optionally
    @self.on_connect / @self.on_disconnect.
    """

    def __init__(self, url: str, logger: Optional[logging.Logger] = None) -> None:
        """
        Args:
            url: Socket.IO server URL.
            logger: Optional logger; if None, logging is disabled.
        """
        self.url = url
        self.logger = logger
        self._stop_event = threading.Event()
        self._connected = False

        # storage for event bindings (so they persist across reconnects)
        self._event_handlers: list[tuple[str, Callable]] = []

        self._connect_callback: Optional[Callable[[], None]] = None
        self._disconnect_callback: Optional[Callable[[], None]] = None

        self._setup_sio()

    # ------------------- Internal setup -------------------

    def _setup_sio(self):
        """Create a new Socket.IO client and bind all known handlers."""
        self._sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1,
            reconnection_delay_max=10,
        )
        self._sio.on('connect', self._handle_connect)
        self._sio.on('disconnect', self._handle_disconnect)

        # reattach any stored event handlers
        for event_name, func in self._event_handlers:
            self._sio.on(event_name, func)

    # ------------------- Decorators for subclasses -------------------

    def on(self, event_name: str):
        """
        Decorator to register a handler for a custom Socket.IO event.

        Usage:
            @self.on('race-table-update')
            def handle(data):
                ...
        """
        def decorator(func):
            # store handler for future rebinds
            self._event_handlers.append((event_name, func))
            self._sio.on(event_name, func)
            return func
        return decorator

    def on_connect(self, func: Callable[[], None]):
        """Optional decorator to register a connect callback."""
        self._connect_callback = func
        return func

    def on_disconnect(self, func: Callable[[], None]):
        """Optional decorator to register a disconnect callback."""
        self._disconnect_callback = func
        return func

    # ------------------- Internal event handlers -------------------

    def _handle_connect(self):
        """Post connect callback."""
        self._connected = True
        self._log(logging.INFO, "Connected to server")
        if self._connect_callback:
            try:
                self._connect_callback()
            except Exception as e: # pylint: disable=broad-except
                self._log(logging.ERROR, f"Error in on_connect callback: {e}")

    def _handle_disconnect(self):
        """Post disconnect callback."""
        self._connected = False
        self._log(logging.INFO, "Disconnected from server")
        if self._disconnect_callback:
            try:
                self._disconnect_callback()
            except Exception as e: # pylint: disable=broad-except
                self._log(logging.ERROR, f"Error in on_disconnect callback: {e}")

    # ------------------- Public API -------------------

    def run(self) -> None:
        """[BLOCKING] Run the client in a loop and reconnect on failure."""
        while not self._stop_event.is_set():
            try:
                self._log(logging.INFO, f"Connecting to {self.url} ...")
                self._sio.connect(self.url, wait=True, transports=["websocket", "polling"])
                self._connected = True
                self._log(logging.INFO, "Connection established")

                while not self._stop_event.is_set() and self._connected:
                    self._sio.sleep(0.1)

            except socketio.exceptions.ConnectionError:
                self._log(logging.WARNING, "Connection failed, retrying...")
                time.sleep(1)
            except Exception as e: # pylint: disable=broad-except
                self._log(logging.ERROR, f"Unexpected error: {e}")
                time.sleep(2)
            finally:
                # Full cleanup to avoid WebSocket session stuck state
                if self._connected:
                    try:
                        self._sio.disconnect()
                    except Exception: # pylint: disable=broad-except
                        pass
                    self._connected = False

                # fully recreate client and rebind all events
                if not self._stop_event.is_set():
                    self._setup_sio()

    def stop(self) -> None:
        """Thread-safe stop method."""
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        if self._connected:
            self._log(logging.INFO, "Disconnecting from server...")
            try:
                self._sio.disconnect()
            except Exception as e: # pylint: disable=broad-except
                self._log(logging.ERROR, f"Error during disconnect: {e}")
            finally:
                self._connected = False

    # ------------------- Internal logging -------------------

    def _log(self, level: int, msg: str) -> None:
        """Log a message, using the logger if available."""
        if self.logger:
            self.logger.log(level, msg)

# ------------------------- EXAMPLES -----------------------------------------------------------------------------------
# TODO: remove

class RaceTableClient(BaseSubscriber):
    def __init__(self, url: str, logger: Optional[logging.Logger] = None):
        super().__init__(url, logger)

        # optional connect/disconnect hooks
        @self.on_connect
        def connected():
            self._log(logging.INFO, "[RaceTableClient] Connected")
            self._sio.emit('register-client', {
                'type': 'race-table',
                'id': 'race-table-client',
                })

        @self.on_disconnect
        def disconnected():
            self._log(logging.INFO, "[RaceTableClient] Disconnected")

        # custom event handler
        @self.on('race-table-update')
        def handle_race_table(data):
            self._log(logging.INFO, f"[RaceTableClient] Received race-table-update ({len(data)} bytes)")

def get_logger(name: str = None, to_stdout: bool = True) -> logging.Logger:
    """Return a logger that writes to stdout if enabled, else a dummy logger."""
    logger = logging.getLogger(name)

    # Clear previous handlers to avoid duplication if reused
    logger.handlers.clear()

    if to_stdout:
        import sys # pylint: disable=import-outside-toplevel
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Dummy (no-op) configuration
        logger.addHandler(logging.NullHandler())

    return logger

if __name__ == "__main__":
    try:
        client = RaceTableClient(url="http://localhost:4768", logger=get_logger())
        client.run()
    except KeyboardInterrupt:
        client.stop()
