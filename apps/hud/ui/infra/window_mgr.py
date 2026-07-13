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
from typing import Any, Callable, Dict, Optional, Tuple, Type

from PySide6.QtCore import (QMetaObject, QMutex, QMutexLocker, QObject, Qt,
                            QTimer, QtMsgType, QWaitCondition, Signal, Slot,
                            qInstallMessageHandler)
from PySide6.QtWidgets import QApplication

from apps.hud.ui.infra.hf_types import HighFreqBase
from apps.hud.ui.overlays import BaseOverlay
from lib.event_counter import EventCounter
from lib.logger import PngLogger
from lib.mailbox import LatestSlot

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

# Topics carrying an idempotent full-state snapshot: coalescing to the latest value is safe.
# Everything else is an imperative command (e.g. toggle/step actions) where every message must
# be processed in order, so it is excluded from coalescing.
STATE_TOPICS = frozenset({
    "race_table_update",
    "stream_overlay_update",
})

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
        self._hf_slots: Dict[str, LatestSlot[HighFreqBase]] = {}  # hf_type -> mailbox; only created for subscribed types
        self._hf_last_seq: Dict[str, int] = {}                    # write-site seq/loss accounting
        self.stats = EventCounter()
        self._state_slots: Dict[str, LatestSlot[Dict[str, Any]]] = {
            topic: LatestSlot(topic, self.stats) for topic in STATE_TOPICS
        }
        self._state_cursors: Dict[Tuple[str, str], int] = {}  # (overlay_id, topic) -> last-read seq

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
            if hf_type not in self._hf_slots:
                self._hf_slots[hf_type] = LatestSlot(hf_type, self.stats)
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

        For a state topic (STATE_TOPICS), the marshaled payload is published to that
        topic's mailbox slot and the signal carries no data - just a doorbell telling
        overlays to pull the latest snapshot (take_state_topic()), coalescing any
        backlog to the newest value. Every other command still carries its payload
        directly on the signal, so it is processed in order, once per message.

        Args:
            cmd (str): Command
            data (Dict[str, Any]): Command data
            high_prio (bool): If True, command is high-priority and should be processed even if overlay is not visible
        """
        self.stats.track_event("__BROADCAST__", cmd)
        marshaled = self._marshal_data(data)
        slot = self._state_slots.get(cmd)
        if slot is not None:
            slot.publish(marshaled)
            self.msg_signal.emit("", high_prio, cmd, None)
        else:
            self.msg_signal.emit("", high_prio, cmd, marshaled)

    def take_state_topic(self, overlay_id: str, cmd: str) -> Optional[Dict[str, Any]]:
        """Pull cmd's mailbox slot for overlay_id, coalescing anything that overlay has
        already seen. Tracks each overlay's read position internally; the caller never
        deals with sequence numbers.

        Callers are expected to only pass a cmd already known to be a state topic (as
        BaseOverlay._handle_cmd does, calling this only when the doorbell signal carried
        no payload) - anything else is a wiring bug, not a runtime condition to handle.

        Returns:
            The marshaled payload, or None if nothing has been published yet or the value
            is unchanged since this overlay's last read.
        """
        slot = self._state_slots.get(cmd)
        assert slot is not None, f"take_state_topic called for non-state topic '{cmd}'"
        key = (overlay_id, cmd)
        pulled = slot.take_if_new(self._state_cursors.get(key, 0))
        if pulled is None:
            return None
        marshaled, seq = pulled
        self._state_cursors[key] = seq
        return marshaled

    def replay_state_topic(self, overlay_id: str, cmd: str) -> Optional[Dict[str, Any]]:
        """Unconditionally read cmd's mailbox slot for overlay_id and update its read
        position to match, regardless of what it has already seen.

        Used for replay-on-show: a freshly visible overlay gets the current value even
        if it is the same one it processed before going invisible, and the cursor update
        means the next ordinary take_state_topic() doesn't redeliver it a second time.

        Returns:
            The marshaled payload, or None if cmd is not a state topic or nothing has
            been published yet.
        """
        slot = self._state_slots.get(cmd)
        if slot is None:
            return None
        pulled = slot.take()
        if pulled is None:
            return None
        marshaled, seq = pulled
        self._state_cursors[(overlay_id, cmd)] = seq
        return marshaled

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
        """Construct high-frequency data and publish it to its mailbox slot, but only if some
        overlay is subscribed to its type (skips the from_json() construction entirely otherwise,
        since that work would otherwise be discarded).

        Called from the IPC thread. LatestSlot.publish() is a single reference swap - atomic
        under the GIL - with no cross-thread signal. Overlay render ticks pull the latest value
        directly via get_latest_hf_data(); there is no per-sample delivery to coalesce.

        Args:
            hf_cls (Type[HighFreqBase]): High-frequency data class to construct via from_json()
            json_data (Dict[str, Any]): Raw payload passed to hf_cls.from_json()
        """
        hf_type = hf_cls.__hf_type__
        slot = self._hf_slots.get(hf_type)
        if slot is None:
            self.stats.track_event("__HF_DROP__", hf_type)
            return

        data = hf_cls.from_json(json_data)
        self._track_hf_write_seq(hf_type, data.__seq__)
        slot.publish(data)

    def get_latest_hf_data(self, hf_type: str) -> Optional[HighFreqBase]:
        """Pull the latest published snapshot for hf_type, or None if nothing has been published yet."""
        slot = self._hf_slots.get(hf_type)
        if slot is None:
            return None
        snapshot = slot.take()
        return snapshot[0] if snapshot is not None else None

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
