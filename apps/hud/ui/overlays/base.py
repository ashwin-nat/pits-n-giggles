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
import os
import sys
from typing import Any, Callable, Dict

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QWidget

from apps.hud.ui.infra.config import OverlaysConfig

# -------------------------------------- TYPES -------------------------------------------------------------------------

OverlayCommandHandler = Callable[[Dict[str, Any]], None] # Takes dict arg, returns None
OverlayRequestHandler = Callable[[Dict[str, Any]], Any] # Takes dict arg, returns Any

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlay(QWidget):
    # Add signal for responses
    response_signal = Signal(str, object)  # request_type, response_data

    def __init__(self, overlay_id: str, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int):
        super().__init__()
        self.overlay_id = overlay_id
        self.config = config
        self.locked = locked
        self.logger = logger
        self.opacity = opacity
        self._drag_pos = None
        self._command_handlers: Dict[str, OverlayCommandHandler] = {}
        self._request_handlers: Dict[str, OverlayRequestHandler] = {}  # New: request handlers
        self._setup_window()
        self.build_ui()
        self.apply_config()

        # Register default request handlers
        self._register_default_handlers()

    # --------------------------------------------------------------------------
    # Setup
    # --------------------------------------------------------------------------
    def _setup_window(self):
        """Apply base window setup and initial flags."""
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.update_window_flags()

    def apply_config(self):
        """Apply initial geometry from config."""
        self.setGeometry(
            self.config.x,
            self.config.y,
            self.config.width,
            self.config.height
        )
        self.setOpacity(self.opacity)

    def setOpacity(self, opacity: int):
        """Set window opacity (0-100)."""
        self.opacity = opacity
        self.logger.debug(f"{self.overlay_id} | Setting opacity to {opacity}%")
        self.setWindowOpacity(self.opacity / 100.0)

    # --------------------------------------------------------------------------
    # Window State
    # --------------------------------------------------------------------------
    def update_window_flags(self):
        """Refresh window flags based on locked state."""
        flags = Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool

        if self.locked:
            flags |= Qt.WindowType.FramelessWindowHint
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)
        else:
            flags |= (
                Qt.WindowType.Window
                | Qt.WindowType.CustomizeWindowHint
            )
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)

        self.setWindowFlags(flags)
        self.show()

    def set_locked_state(self, locked: bool):
        """Set locked state dynamically."""
        self.locked = locked
        self.update_window_flags()

    def get_window_info(self) -> OverlaysConfig:
        """Return current geometry as an OverlaysConfig."""
        geo = self.geometry()
        return OverlaysConfig(
            x=geo.x(),
            y=geo.y(),
            width=geo.width(),
            height=geo.height()
        )

    # --------------------------------------------------------------------------
    # Subclass hooks
    # --------------------------------------------------------------------------
    def build_ui(self):
        """Subclasses must implement this to build their layout."""
        raise NotImplementedError

    # --------------------------------------------------------------------------
    # Command infra
    # --------------------------------------------------------------------------
    def on_command(self, cmd_name: str):
        """Flask-style decorator for registering command handlers."""
        def decorator(func: OverlayCommandHandler):
            self._command_handlers[cmd_name] = func
            return func
        return decorator

    def _register_default_handlers(self):
        """Register built-in request handlers."""
        @self.on_request("get_window_info")
        def handle_get_window_info(_data: Dict[str, Any]):
            self.logger.debug(f'{self.overlay_id} | Received request "get_window_info"')
            # Return actual window info, not dummy values!
            return self.get_window_info()

        @self.on_command("set_locked_state")
        def handle_set_locked_state(data: dict):
            locked = data.get('new-value', False)
            self.logger.debug(f'{self.overlay_id} | Setting locked state to {locked}')
            self.set_locked_state(locked)

        @self.on_command("toggle_visibility")
        def handle_toggle_visibility(_data: dict):
            self.logger.debug(f'{self.overlay_id} | Toggling visibility')
            if self.isVisible():
                self.logger.debug(f'{self.overlay_id} | Hiding overlay')
                self.hide()
            else:
                self.logger.debug(f'{self.overlay_id} | Showing overlay')
                self.show()

    def on_request(self, request_type: str):
        """Decorator for registering request handlers that return responses."""
        def decorator(func: Callable[[dict], Any]):
            self._request_handlers[request_type] = func
            return func
        return decorator

    @Slot(str, str, dict)
    def _handle_request(self, recipient: str, request_type: str, request_data: dict):
        """Internal request dispatcher for overlays."""
        if recipient and recipient != self.overlay_id:
            return  # Not for this overlay

        if handler := self._request_handlers.get(request_type):
            self.logger.debug(f"{self.overlay_id} | Handling request '{request_type}'")
            parsed_data = json.loads(request_data)
            try:
                response = handler(parsed_data)
                # Emit response back through window manager
                self.response_signal.emit(request_type, response)
            except Exception as e: # pylint: disable=broad-except
                self.logger.exception(f"{self.overlay_id} | Error handling request '{request_type}': {e}")
        else:
            self.logger.debug(f"{self.overlay_id} | No handler for request '{request_type}'")

    # Existing _handle_cmd method stays the same
    @Slot(str, str, str)
    def _handle_cmd(self, recipient: str, cmd: str, data: str):
        """Internal command dispatcher for overlays."""
        if recipient and recipient != self.overlay_id:
            return  # Not for this overlay

        if handler := self._command_handlers.get(cmd):
            parsed_data = json.loads(data)
            try:
                handler(parsed_data)
            except Exception as e: # pylint: disable=broad-except
                self.logger.exception(f"{self.overlay_id} | Error handling command '{cmd}': {e}")
        else:
            self.logger.warning(f"{self.overlay_id} | No handler registered for command '{cmd}'")

    # --------------------------------------------------------------------------
    # Mouse interactions (dragging + resizing only)
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if not self.locked and event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.locked and event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        event.accept()

    def load_icon(self, relative_path: str) -> QIcon:
        """
        Load an icon that works in both dev and PyInstaller builds.

        Args:
            relative_path: Path to the icon file, relative to the project root or build bundle.

        Returns:
            QIcon: The loaded icon, or an empty QIcon if loading fails.
        """
        try:
            if hasattr(sys, "_MEIPASS"):
                # Running inside a PyInstaller bundle
                base_path = sys._MEIPASS
            else:
                # Running from source
                base_path = os.path.abspath(".")

            full_path = os.path.join(base_path, relative_path)
            return QIcon(full_path)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.warning(f"{self.overlay_id} | Failed to load icon '{relative_path}': {e}")
            return QIcon()

    # --------------------------------------------------------------------------
    # Data handling helpers
    # --------------------------------------------------------------------------

    def _get_ref_row_index(self, data: dict) -> int:
        """Helper to get the reference row index from incoming race table data."""
        if not data or "table-entries" not in data or not data["table-entries"]:
            return None

        is_spectating = data.get("is-spectating", False)
        spectator_index = data.get("spectator-car-index")

        if is_spectating and spectator_index is not None:
            if 0 <= spectator_index < len(data["table-entries"]):
                return spectator_index
            self.logger.warning(f"Warning: Spectator index {spectator_index} is out of bounds.")
            return None

        return next(
            (
                index
                for index, row in enumerate(data["table-entries"])
                if row.get("driver-info", {}).get("is-player") is True
            ),
            None,
        )

    def _get_ref_row(self, data: dict) -> dict:
        """Helper to get the reference row from incoming race table data."""

        ref_index = self._get_ref_row_index(data)
        return None if ref_index is None else data["table-entries"][ref_index]
