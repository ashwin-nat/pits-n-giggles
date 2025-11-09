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

import base64
import ctypes
import json
import logging
import os
import time
import traceback
from threading import Lock, Thread
from typing import Dict, Optional

import win32con
import win32gui
from PySide6.QtCore import QObject, Signal

from .config import OverlaysConfig
from apps.hud.ui.overlays import BaseOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WindowManager(QObject):
    # Define signals for broadcasting data
    data_updated = Signal(dict)
    locked_state_changed = Signal(bool)
    # Signal for sending data to specific overlay (window_id, data)
    overlay_data_updated = Signal(str, dict)

    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.overlays: Dict[str, BaseOverlay] = {}

    def register_overlay(self, window_id: str, overlay: BaseOverlay):
        """Register an overlay and connect signals to its slots."""
        self.logger.debug(f"Registering overlay {window_id}")
        self.overlays[window_id] = overlay

        # Connect broadcast signal to overlay's update_data slot
        self.data_updated.connect(overlay.update_data)

        # Connect targeted signal using a lambda to filter by window_id
        self.overlay_data_updated.connect(
            lambda target_id, data, overlay=overlay, window_id=window_id:
                overlay.update_data(data) if target_id == window_id else None
        )

    def unregister_overlay(self, window_id: str):
        """Unregister an overlay and disconnect its signals."""
        if window_id in self.overlays:
            overlay = self.overlays[window_id]
            # Disconnect all signals from this overlay
            try:
                self.data_updated.disconnect(overlay.update_data)
            except RuntimeError:
                pass  # Already disconnected
            del self.overlays[window_id]
            self.logger.debug(f"Unregistered overlay {window_id}")

    def set_locked_state_all(self, args: Dict[str, bool]):
        """Set locked state for all overlays."""
        locked = args['new-value']
        for name, overlay in self.overlays.items():
            self.logger.debug(f"Setting locked state for overlay {name}. locked={locked}")
            overlay.set_locked_state(locked)

        # Emit signal for any other listeners
        self.locked_state_changed.emit(locked)

    def race_table_update(self, data: dict):
        """Update all overlays with race table data."""
        self.logger.debug("Broadcasting race table update")
        self.broadcast_data(data)

    def toggle_visibility_all(self):
        """Toggle visibility for all overlays."""
        for name, overlay in self.overlays.items():
            if overlay.isVisible():
                overlay.hide()
                self.logger.debug(f"Hiding overlay {name}")
            else:
                overlay.show()
                self.logger.debug(f"Showing overlay {name}")

    def stop(self):
        """Stop and cleanup all overlays."""
        self.logger.info("Stopping WindowManager and cleaning up overlays")
        for window_id in list(self.overlays.keys()):
            self.unregister_overlay(window_id)

    def broadcast_data(self, data: dict):
        """Broadcast data to all registered overlays using signal."""
        self.logger.debug(f"Broadcasting data to {len(self.overlays)} overlays")
        self.data_updated.emit(data)

    def send_data_to_overlay(self, window_id: str, data: dict):
        """Send data to a specific overlay using signal."""
        if window_id in self.overlays:
            self.logger.debug(f"Sending data to overlay {window_id}")
            self.overlay_data_updated.emit(window_id, data)
        else:
            self.logger.warning(f"Overlay {window_id} not found")

    def get_window_info(self, window_id: str) -> OverlaysConfig:
        """Get window configuration for a specific overlay."""
        if window_id in self.overlays:
            return self.overlays[window_id].get_window_info()
        self.logger.warning(f"Overlay {window_id} not found, returning default config")
        return OverlaysConfig(x=0, y=0, width=0, height=0)

    def get_all_window_info(self) -> Dict[str, OverlaysConfig]:
        """Get window configurations for all overlays."""
        return {
            window_id: overlay.get_window_info()
            for window_id, overlay in self.overlays.items()
        }
