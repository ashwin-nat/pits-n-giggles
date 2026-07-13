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

import os
from time import perf_counter_ns
from typing import Any, Callable, Dict, Optional, Type

from PySide6.QtCore import (QMetaObject, QMutex, QMutexLocker, QObject, Qt,
                            QTimer, QtMsgType, QWaitCondition, Signal, Slot,
                            qInstallMessageHandler)
from PySide6.QtWidgets import QApplication

from apps.hud.ui.infra.hf_types import HighFreqBase
from apps.hud.ui.overlays import BaseOverlay
from lib.event_counter import EventCounter
from lib.logger import PngLogger

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WindowManager(QObject):

    msg_signal = Signal(str, bool, str, object)  # recipient (empty = broadcast), priority, event, data
    mgmt_request_signal = Signal(str, str, object)  # recipient, request_type, request_data
    mgmt_response_signal = Signal(str, object)     # request_type, response_data

    def __init__(self, logger: PngLogger, post_init_cb: Optional[Callable[[], None]] = None):
        """Initialize window manager.

        Args:
            logger: Logger
        """
        os.environ.setdefault("QSG_RENDER_LOOP", "threaded")
        self.app = QApplication()
        super().__init__()
        self.logger = logger
        self.logger.silent("QSG_RENDER_LOOP = %s", os.environ.get("QSG_RENDER_LOOP", "(not set)"))
        self.overlays: Dict[str, BaseOverlay] = {}
        self._hf_mailbox: Dict[str, HighFreqBase] = {}   # hf_type -> latest snapshot
        self._hf_subscriber_types: set = set()           # hf_types at least one overlay subscribes to
        self._hf_last_seq: Dict[str, int] = {}           # write-site seq/loss accounting
        self.stats = EventCounter()

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
        assert overlay_id not in self.overlays, f"Overlay ID {overlay_id} is already registered"
        self.logger.debug("Registering overlay %s", overlay_id)
        self.overlays[overlay_id] = overlay

        # Connect broadcast command and request signals TO the overlay
        self.msg_signal.connect(overlay._handle_cmd)
        self.mgmt_request_signal.connect(overlay._handle_request)

        # Connect overlay's response signal back to manager
        overlay.response_signal.connect(self.mgmt_response_signal.emit)

        # Let the overlay pull HF data straight from this manager's mailbox instead
        # of receiving it via a per-sample queued signal.
        overlay.set_window_manager(self)
        for hf_type in overlay._hf_subscriptions:
            self._hf_subscriber_types.add(hf_type)
            self.logger.debug("Overlay %s subscribed to HF type '%s'", overlay_id, hf_type)

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
                self.stats.track_event("__REQUEST_OK__", request_type)
                return self._response_data
            self.logger.warning("Request timeout: %s to %s", request_type, recipient or 'manager')
            self.stats.track_event("__REQUEST_TIMEOUT__", request_type)
            return None

    # Keep existing methods for GUI thread use
    def broadcast_data(self, cmd: str, data: Dict[str, Any], high_prio: bool = False):
        """Broadcast event data to all registered overlays using signal.

        Args:
            cmd (str): Command
            data (Dict[str, Any]): Command data
            high_prio (bool): If True, command is high-priority and should be processed even if overlay is not visible
        """
        self.stats.track_event("__BROADCAST__", cmd)
        self.msg_signal.emit("", high_prio, cmd, self._marshal_data(data))

    def unicast_data(self, overlay_id: str, event: str, data: Dict[str, Any], high_prio: bool = False):
        """Unicast event data to a specific overlay using ssignal.

        Args:
            overlay_id (str): Overlay ID
            event (str): Command
            data (Dict[str, Any]): Command data
            high_prio (bool): If True, command is high-priority and should be processed even if overlay is not visible
        """
        assert overlay_id
        self.stats.track_event("__UNICAST__", event)
        self.msg_signal.emit(overlay_id, high_prio, event, self._marshal_data(data))

    def send_high_freq_data(self, hf_cls: Type[HighFreqBase], json_data: Dict[str, Any]) -> None:
        """Construct high-frequency data and publish it to the mailbox, but only if some overlay
        is subscribed to its type (skips the from_json() construction entirely otherwise, since
        that work would otherwise be discarded).

        Called from the IPC thread. Writes a single reference into self._hf_mailbox - atomic
        under the GIL - with no cross-thread signal. Overlay render ticks pull the latest value
        directly via get_latest_hf_data(); there is no per-sample delivery to coalesce.

        Args:
            hf_cls (Type[HighFreqBase]): High-frequency data class to construct via from_json()
            json_data (Dict[str, Any]): Raw payload passed to hf_cls.from_json()
        """
        hf_type = hf_cls.__hf_type__
        if hf_type not in self._hf_subscriber_types:
            self.stats.track_event("__HF_DROP__", hf_type)
            return

        data = hf_cls.from_json(json_data)
        self._track_hf_write_seq(hf_type, data.__seq__)
        self.stats.track_event("__HF_SEND__", hf_type)
        self._hf_mailbox[hf_type] = data

    def get_latest_hf_data(self, hf_type: str) -> Optional[HighFreqBase]:
        """Pull the latest published snapshot for hf_type, or None if nothing has been published yet."""
        return self._hf_mailbox.get(hf_type)

    def _track_hf_write_seq(self, hf_type: str, curr_seq: int) -> None:
        """Write-site seq/loss accounting - a single pass per hf_type instead of one per subscriber."""
        prev_seq = self._hf_last_seq.get(hf_type)
        if prev_seq is not None and curr_seq > prev_seq + 1:
            lost = curr_seq - prev_seq - 1
            self.stats.track_event("__HF_LOSS__", "__TOTAL__", count=lost)
            self.stats.track_event("__HF_LOSS__", hf_type, count=lost)
        self._hf_last_seq[hf_type] = curr_seq

    def _marshal_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp to payload."""
        return {
            "__meta__" : {
                "__timestamp__" : perf_counter_ns(),
            },
            "__payload__": payload
        }

    def get_stats(self) -> dict:
        return self.stats.get_stats()
