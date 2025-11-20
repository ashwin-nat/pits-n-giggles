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
from typing import Callable, Optional

import msgpack
import socketio

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class IpcSubscriber:
    """
    Base class for a synchronous Socket.IO client running in its own thread.
    Subclasses register events via @self.on('event-name') and optionally
    @self.on_connect / @self.on_disconnect.
    """

    def __init__(self,
                 url: str,
                 logger: Optional[logging.Logger] = None,
                 msg_packed: bool = False
                 ) -> None:
        """
        Args:
            url: Socket.IO server URL.
            logger: Optional logger; if None, logging is disabled.
            msg_packed: Whether to use msgpack for message de-serialization.
        """
        self.url = url
        self.logger = logger
        self._stop_event = threading.Event()
        self._connected = False
        self._msg_packed = msg_packed

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
        Automatically unpacks msgpack data if self._msg_packed is True.
        """
        def decorator(func):
            # wrap the user's handler to decode msgpack if needed
            if self._msg_packed:
                def wrapped_handler(data):
                    try:
                        decoded = msgpack.unpackb(data, raw=False)
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self._log(logging.ERROR, f"Failed to decode msgpack for event '{event_name}': {e}")
                        return  # consistently returns None
                    func(decoded)  # call handler without returning its value
            else:
                wrapped_handler = func

            # store handler for future rebinds
            self._event_handlers.append((event_name, wrapped_handler))
            self._sio.on(event_name, wrapped_handler)
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
        self._log(logging.DEBUG, "Connected to server")
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

        self._log(logging.DEBUG, "IPC subscriber. Finished run loop")

    def stop(self) -> None:
        """Thread-safe stop method."""
        if self._stop_event.is_set():
            return
        self._log(logging.INFO, "Stopping IPC subscriber...")
        self._stop_event.set()
        if self._connected:
            self._log(logging.DEBUG, "Disconnecting from server...")
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
            self.logger.log(level, msg, stacklevel=2)
