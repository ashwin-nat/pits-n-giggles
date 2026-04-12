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
from time import perf_counter_ns
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import (QMetaObject, QMutex, QMutexLocker, QObject,
                            QTimer, QWaitCondition, Qt, QtMsgType, Signal,
                            Slot, qInstallMessageHandler)
from PySide6.QtWidgets import QApplication

from apps.hud.ui.infra.hf_types import HighFreqBase
from apps.hud.ui.overlays import BaseOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WindowManager(QObject):

    generic_cmd_signal = Signal(str, bool, str, object)  # recipient (empty = broadcast), priority, event, data
    mgmt_request_signal = Signal(str, str, object)  # recipient, request_type, request_data
    mgmt_response_signal = Signal(str, object)     # request_type, response_data
    mgmt_high_freq_signal = Signal(object) # HighFreqBase

    def __init__(self, logger: logging.Logger, post_init_cb: Optional[Callable[[], None]] = None):
        """Initialize window manager.

        Args:
            logger: Logger
        """
        self.app = QApplication()
        super().__init__()
        self.logger = logger
        self.overlays: Dict[str, BaseOverlay] = {}

        qInstallMessageHandler(self._qt_message_handler)

        # Request/response infrastructure
        self._response_mutex = QMutex()
        self._response_condition = QWaitCondition()
        self._response_data: Optional[Any] = None
        self._response_received = False

        # Connect signals
        self.mgmt_request_signal.connect(self._handle_request)
        self.mgmt_response_signal.connect(self._store_response)

        if post_init_cb:
            # Will be called once the event loop is running
            QTimer.singleShot(0, post_init_cb)

    def run(self):
        """Start the Qt event loop."""
        self.app.exec()

    def stop(self):
        """Request the Qt event loop to stop (thread-safe)."""
        QMetaObject.invokeMethod(self.app, "quit", Qt.ConnectionType.QueuedConnection)

    def _qt_message_handler(self, mode: QtMsgType, _, message: str):
        if mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            self.logger.error("[Qt] %s", message)
        elif mode == QtMsgType.QtWarningMsg:
            self.logger.warning("[Qt] %s", message)
        else:
            self.logger.debug("[Qt] %s", message)

    def register_overlay(self, overlay_id: str, overlay: BaseOverlay):
        """Register an overlay and connect signals to its slots."""
        self.logger.debug("Registering overlay %s", overlay_id)
        self.overlays[overlay_id] = overlay

        # Connect command and request signals TO the overlay
        self.generic_cmd_signal.connect(overlay._handle_cmd)
        self.mgmt_request_signal.connect(overlay._handle_request)
        self.mgmt_high_freq_signal.connect(overlay._handle_high_freq_data)

        # Connect overlay's response signal back to manager
        overlay.response_signal.connect(self.mgmt_response_signal.emit)

    # pylint: disable=useless-return
    @Slot(str, str, dict)
    def _handle_request(self, recipient: str, _request_type: str, _request_data: str):
        """Handle requests on GUI thread - manager-level requests only."""
        if recipient:
            return  # Overlay-specific requests handled by overlay

        # No manager-level requests currently needed
        # All requests go directly to overlays

    @Slot(str, object)
    def _store_response(self, request_type: str, response_data: Any):
        """Store response and wake waiting thread."""
        with QMutexLocker(self._response_mutex):
            self._response_data = response_data
            self._response_received = True
            self.logger.debug("Received response: %s. Reponse=%s", request_type, response_data)
            self._response_condition.wakeAll()

    def request(self, recipient: str, request_type: str,
                request_data: Dict[str, Any] = None, timeout_ms: int = 5000) -> Dict[str, Any]:
        """
        Make a blocking request and wait for response.

        Args:
            recipient: Target overlay ID (empty string for manager-level request)
            request_type: Type of request (e.g., "get_window_info")
            request_data: Optional request parameters
            timeout_ms: Maximum time to wait for response

        Returns:
            Response data or None on timeout
        """
        with QMutexLocker(self._response_mutex):
            # Reset response state
            self._response_data = None
            self._response_received = False

            # Emit request
            self.mgmt_request_signal.emit(recipient, request_type, request_data)

            # Wait for response
            if self._response_condition.wait(self._response_mutex, timeout_ms):
                return self._response_data
            self.logger.warning("Request timeout: %s to %s", request_type, recipient or 'manager')
            return None

    # Keep existing methods for GUI thread use
    def broadcast_data(self, cmd: str, data: Dict[str, Any], high_prio: bool = False):
        """Broadcast event data to all registered overlays using signal.

        Args:
            cmd (str): Command
            data (Dict[str, Any]): Command data
            high_prio (bool): If True, command is high-priority and should be processed even if overlay is not visible
        """
        self.generic_cmd_signal.emit("", high_prio, cmd, self._marshal_data(data))

    def unicast_data(self, overlay_id: str, event: str, data: Dict[str, Any], high_prio: bool = False):
        """Unicast event data to a specific overlay using signal.

        Args:
            overlay_id (str): Overlay ID
            event (str): Command
            data (Dict[str, Any]): Command data
            high_prio (bool): If True, command is high-priority and should be processed even if overlay is not visible
        """
        assert overlay_id
        self.generic_cmd_signal.emit(overlay_id, high_prio, event, self._marshal_data(data))

    def send_high_freq_data(self, data: HighFreqBase):
        """Send high-frequency data to all subscribed overlays.

        Args:
            data (HighFreqBase): High-frequency data payload
        """
        self.mgmt_high_freq_signal.emit(data)

    def _marshal_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp to payload."""
        return {
            "__meta__" : {
                "__timestamp__" : perf_counter_ns(),
            },
            "__payload__": payload
        }
