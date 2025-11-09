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
from abc import abstractmethod

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from apps.hud.ui.infra.config import OverlaysConfig

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlay(QWidget):
    """Base class for all display-only overlays (e.g., lap timer, tyre info, etc.)."""

    def __init__(self, overlay_id: str, config: OverlaysConfig, logger: logging.Logger, locked: bool = False):
        super().__init__()
        self.overlay_id = overlay_id
        self.config = config
        self.locked = locked
        self.logger = logger
        self._drag_pos = None
        self._setup_window()
        self.build_ui()
        self.apply_config()

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

    @Slot(str, str, dict)
    def _handle_cmd(self, recipient: str, cmd: str, data: dict):
        """Subclasses implement to refresh their displayed data."""
        self.logger.debug(f"Received data. recipient: {recipient}, cmd: {cmd}")
        if ('' == recipient) or (recipient == self.id):
            self.logger.debug(f"Handling data. cmd: {cmd}")

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

    # --------------------------------------------------------------------------
    # Data handling helpers
    # --------------------------------------------------------------------------
    def _get_ref_row(self, data: dict) -> dict:
        """Helper to get the reference row from incoming race table data."""

        if not data or "table-entries" not in data or not data["table-entries"]:
            return None

        is_spectating = data.get("is-spectating", False)
        spectator_index = data.get("spectator-car-index")

        if is_spectating and spectator_index is not None:
            if 0 <= spectator_index < len(data["table-entries"]):
                return data["table-entries"][spectator_index]
            else:
                self.logger.warning(f"Warning: Spectator index {spectator_index} is out of bounds.")
                return None
        else:
            for row in data["table-entries"]:
                if row.get("driver-info", {}).get("is-player") is True:
                    return row
            return None
