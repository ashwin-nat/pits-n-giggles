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
from typing import Callable, Optional

import engineio.exceptions
import msgpack
import socketio.exceptions

from lib.event_counter import EventCounter

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SocketioClient:
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
            msg_packed: Whether to use msgpack for message decoding
        """
        self.url = url

    # If no logger provided, create a no-op logger
        if logger is None:
            logger = logging.getLogger(f"IpcSubscriber:{id(self)}")
            logger.addHandler(logging.NullHandler())
        self.logger = logger
        self._stop_event = threading.Event()
        self._connected = False
        self._msg_packed = msg_packed
        self.stats = EventCounter()

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
            def wrapped_handler(data):
                self.stats.track_event("__SOCKET_IN__", "__TOTAL__")
                self.stats.track_event("__SOCKET_IN__", event_name)

                payload_size = self._get_payload_size(data)
                if payload_size is not None:
                    self.stats.track_packet("__SOCKET_IN_PAYLOAD__", "__TOTAL__", payload_size)
                    self.stats.track_packet("__SOCKET_IN_PAYLOAD__", event_name, payload_size)

                if self._msg_packed:
                    try:
                        decoded = msgpack.unpackb(data, raw=False)
                    except (TypeError, ValueError) as e:
                        # Likely a Socket.IO internal packet, just ignore
                        self.stats.track_event("__DROP__", "invalid_msgpack")
                        self.stats.track_event("__DROP_EVENT__", event_name)
                        self.logger.warning(
                            "Skipping non-msgpack data for event %s (likely internal packet): %s. Error: %s",
                            event_name, str(data), e
                        )
                        return
                    except Exception as e: # pylint: disable=broad-exception-caught
                        self.stats.track_event("__ERROR__", "decode_msgpack_exception")
                        self.stats.track_event("__DECODE_ERROR_EVENT__", event_name)
                        self.logger.exception("Failed to decode msgpack for event %s: %s %s", event_name, e, data)
                        return  # consistently returns None
                    callback_data = decoded
                else:
                    callback_data = data

                try:
                    func(callback_data)
                    self.stats.track_event("__HANDLER__", "success")
                    self.stats.track_event("__HANDLED_EVENT__", event_name)
                except Exception:  # pylint: disable=broad-exception-caught
                    self.stats.track_event("__ERROR__", "handler_exception")
                    self.stats.track_event("__HANDLER_ERROR_EVENT__", event_name)
                    raise

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
        self.stats.track_event("__CONNECTIVITY__", "connected")
        self.logger.debug("Connected to server")
        if self._connect_callback:
            try:
                self._connect_callback()
            except Exception as e: # pylint: disable=broad-exception-caught
                self.stats.track_event("__ERROR__", "on_connect_callback_exception")
                self.logger.exception("Error in on_connect callback: %s", e)

    def _handle_disconnect(self):
        """Post disconnect callback."""
        self._connected = False
        self.stats.track_event("__CONNECTIVITY__", "disconnected")
        self.logger.debug("Disconnected from server")
        if self._disconnect_callback:
            try:
                self._disconnect_callback()
            except Exception as e: # pylint: disable=broad-exception-caught
                self.stats.track_event("__ERROR__", "on_disconnect_callback_exception")
                self.logger.exception("Error in on_disconnect callback: %s", e)

    # ------------------- Public API -------------------

    def run(self) -> None:
        """[BLOCKING] Run the client with automatic retry supervision."""
        self.logger.debug("Starting IPC subscriber run loop")

        while not self._stop_event.is_set():

            try:
                if not self._connected:
                    self.logger.debug("Attempting connection to %s ...", self.url)
                    self.stats.track_event("__CONNECTIVITY__", "connect_attempt")
                    self._sio.connect(
                        self.url,
                        wait=True,
                        transports=["websocket", "polling"],
                    )
                    self.logger.debug("Connection established")

                while not self._stop_event.is_set() and self._connected:
                    self._sio.sleep(0.1)

            except (
                socketio.exceptions.ConnectionError,
                engineio.exceptions.ConnectionError,
                ConnectionRefusedError,
            ) as e:
                self.stats.track_event("__ERROR__", "connect_error")
                self.logger.debug("Connection error (%s). Will retry...", e)

            except Exception as e:  # pylint: disable=broad-exception-caught
                self.stats.track_event("__ERROR__", "run_loop_exception")
                self.logger.exception("Unexpected error: %s", e)

            finally:
                if self._connected:
                    try:
                        self._sio.disconnect()
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        self.stats.track_event("__ERROR__", "disconnect_error")
                        self.logger.exception("Error during disconnect: %s", e)

            if not self._stop_event.is_set():
                self.logger.debug("Waiting before retry...")
                self._stop_event.wait(2.0)

        self.logger.debug("IPC subscriber. Finished run loop")

    def stop(self) -> None:
        """Thread-safe stop method."""
        if self._stop_event.is_set():
            return
        self.logger.debug("Stopping IPC subscriber...")
        self._stop_event.set()
        if self._connected:
            self.logger.debug("Disconnecting from server...")
            try:
                self._sio.disconnect()
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.exception("Error during disconnect: %s", e)
            finally:
                self._connected = False

    def get_stats(self) -> dict:
        """Get current socketio client stats snapshot."""
        return self.stats.get_stats()

    @staticmethod
    def _get_payload_size(payload: object) -> Optional[int]:
        """Best-effort payload length for traffic stats."""
        if isinstance(payload, (bytes, bytearray, memoryview, str)):
            return len(payload)
        return None
