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
from typing import Dict, Optional, Any

from PySide6.QtCore import QObject, Signal, Slot, QMutex, QWaitCondition, QMutexLocker

from apps.hud.ui.overlays import BaseOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WindowManager(QObject):
    # Existing signal
    mgmt_cmd_signal = Signal(str, str, str)  # recipient, cmd, data (serialised into string)

    # New request/response signals
    mgmt_request_signal = Signal(str, str, str)  # recipient, request_type, request_data
    mgmt_response_signal = Signal(str, object)     # request_type, response_data

    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.overlays: Dict[str, BaseOverlay] = {}

        # Request/response infrastructure
        self._response_mutex = QMutex()
        self._response_condition = QWaitCondition()
        self._response_data: Optional[Any] = None
        self._response_received = False

        # Connect signals
        self.mgmt_request_signal.connect(self._handle_request)
        self.mgmt_response_signal.connect(self._store_response)

    def register_overlay(self, overlay_id: str, overlay: BaseOverlay):
        """Register an overlay and connect signals to its slots."""
        self.logger.debug(f"Registering overlay {overlay_id}")
        self.overlays[overlay_id] = overlay

        # Connect command and request signals TO the overlay
        self.mgmt_cmd_signal.connect(overlay._handle_cmd)
        self.mgmt_request_signal.connect(overlay._handle_request)

        # **CRITICAL FIX**: Connect overlay's response signal back to manager
        overlay.response_signal.connect(self.mgmt_response_signal.emit)

    def unregister_overlay(self, overlay_id: str):
        """Unregister an overlay and disconnect its signals."""
        if overlay_id in self.overlays:
            overlay = self.overlays[overlay_id]
            # Disconnect all signals from this overlay
            try:
                self.mgmt_cmd_signal.disconnect(overlay._handle_cmd)
                self.mgmt_request_signal.disconnect(overlay._handle_request)
                overlay.response_signal.disconnect(self.mgmt_response_signal.emit)
            except RuntimeError:
                pass  # Already disconnected
            del self.overlays[overlay_id]
            self.logger.debug(f"Unregistered overlay {overlay_id}")

    # pylint: disable=useless-return
    @Slot(str, str, dict)
    def _handle_request(self, recipient: str, _request_type: str, _request_data: dict):
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
            self.logger.debug(f"Received response: {request_type}. Reponse={response_data}")
            self._response_condition.wakeAll()

    def request(self, recipient: str, request_type: str,
                request_data: dict = None, timeout_ms: int = 5000) -> Optional[Any]:
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
            self.mgmt_request_signal.emit(recipient, request_type, json.dumps(request_data,separators=(',', ':')) or {})

            # Wait for response
            if self._response_condition.wait(self._response_mutex, timeout_ms):
                return self._response_data
            self.logger.warning(f"Request timeout: {request_type} to {recipient or 'manager'}")
            return None

    # Keep existing methods for GUI thread use
    def broadcast_data(self, cmd: str, data: dict):
        """Broadcast data to all registered overlays using signal."""
        # self.logger.debug(f"Broadcasting data to {len(self.overlays)} overlays")
        self.mgmt_cmd_signal.emit('', cmd, json.dumps(data, separators=(',', ':')))

    def unicast_data(self, overlay_id: str, cmd: str, data: dict):
        """Unicast data to a specific overlay using signal."""
        self.logger.debug(f"Unicasting data to overlay {overlay_id}")
        self.mgmt_cmd_signal.emit(overlay_id, cmd, json.dumps(data, separators=(',', ':')))
