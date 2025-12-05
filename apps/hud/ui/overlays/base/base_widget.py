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

import ctypes
from pathlib import Path

from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from lib.assets_loader import load_icon
from meta.meta import APP_NAME_SNAKE
from typing import override

from .base import BaseOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlayWidget(BaseOverlay, QWidget):

    def __init__(self,
                 overlay_id,
                 config,
                 logger,
                 locked,
                 opacity,
                 scale_factor,
                 windowed_overlay):

        logger.debug(f"{overlay_id} | Initializing QWidget")

        # Initialize QWidget first (no args needed)
        QWidget.__init__(self)

        logger.debug(f"{overlay_id} | QWidget initialized. Before init of BaseOverlay")

        # Then initialize BaseOverlay with all required args
        BaseOverlay.__init__(
            self,
            overlay_id,
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
        )
        self.adjustSize()

        logger.debug(f"{overlay_id} | BaseOverlay initialized")

        self._drag_pos = None
        self._fade_anim = None

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------
    def _setup_window(self):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME_SNAKE)

        self.setWindowTitle(self.overlay_id)
        self.setWindowIcon(load_icon(Path("assets") / "logo.png",
                                     debug_log_printer=self.logger.debug,
                                     error_log_printer=self.logger.error))

        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")
        self.update_window_flags()
        self.adjustSize()

    # ------------------------------------------------------------------
    # UI build + rebuild
    # ------------------------------------------------------------------
    def apply_config(self):
        self.move(self.config.x, self.config.y)
        self.set_opacity(self.opacity)

    def rebuild_ui(self):
        for w in self.findChildren(QWidget):
            w.setParent(None)
            w.deleteLater()

        layout = self.layout()
        if layout:
            QWidget().setLayout(layout)

        self.build_ui()
        self.update_window_flags()
        self.adjustSize()

    # ------------------------------------------------------------------
    # Window flag logic
    # ------------------------------------------------------------------
    def update_window_flags(self):
        flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint

        if self.windowed_overlay:
            flags |= Qt.Window
        else:
            flags |= Qt.Tool
            if self.locked:
                flags |= Qt.WindowTransparentForInput
            else:
                flags |= Qt.Window | Qt.CustomizeWindowHint | Qt.MSWindowsFixedSizeDialogHint

        self.setWindowFlags(flags)
        self.show()

    # ------------------------------------------------------------------
    # Opacity / Locked State
    # ------------------------------------------------------------------
    def set_opacity(self, opacity: int):
        self.opacity = opacity
        self.setWindowOpacity(opacity / 100.0)

    def set_locked_state(self, locked: bool):
        self.locked = locked
        self.update_window_flags()

    # ------------------------------------------------------------------
    # Fade
    # ------------------------------------------------------------------
    def animate_fade(self, show: bool):
        start, end = (0, 1) if show else (1, 0)

        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(250)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.finished.connect(lambda: self.hide() if not show else None)

        self._fade_anim = anim  # prevent GC

        if show:
            self.setWindowOpacity(0)
            self.show()

        anim.start()

    # ------------------------------------------------------------------
    # Geometry + visibility
    # ------------------------------------------------------------------
    def geometry(self):
        return QWidget.geometry(self)

    def is_visible(self) -> bool:
        return self.isVisible()

    # ------------------------------------------------------------------
    # Dragging
    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if not self.locked and event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.locked and event.buttons() & Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _event: QMouseEvent):
        self._drag_pos = None
