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
from pathlib import Path
from typing import Optional, TypeVar, override

from PySide6.QtCore import (QEvent, QObject, QPoint, QPropertyAnimation, Qt,
                            QTimer, QUrl)
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.infra.hf_types import HighFreqBase

from .base import BaseOverlay

# -------------------------------------- TYPES -------------------------------------------------------------------------

HighFreqObjType = TypeVar("HighFreqObjType", bound=HighFreqBase)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlayQML(BaseOverlay, QObject):
    """
    Base class for all QML-based overlays.

    This is the QML equivalent of BaseOverlayWidget. It satisfies the abstract
    interface required by BaseOverlay and provides:

    --------------------------------------------------------------------------
    WHAT THIS CLASS IMPLEMENTS
    --------------------------------------------------------------------------
    - Loading QML from disk using QQmlApplicationEngine
    - Ownership of the root QML window (QQuickWindow)
    - Applying window flags (always-on-top, frameless, tool vs full window)
    - Position & opacity management via QQuickWindow
    - Fade-in/fade-out via QPropertyAnimation bound to QQuickWindow.opacity
    - Rebuilding QML UI when scale factor changes
    - Allowing locked/unlocked (click-through) behavior via flags
    - Windowed Overlay Mode (OBS capture)

    --------------------------------------------------------------------------
    WHAT DERIVED CLASSES MUST PROVIDE
    --------------------------------------------------------------------------
    - A QML file path passed into constructor or via subclass default
    - Optional extra integration with QML root object
    - QML should expose a root Window {} or Item {} inside a Window {}
    - QML should contain `property real scaleFactor`

    This class does NOT assume anything about the UI structure. Derived classes
    may communicate with QML using:
        - findChild()
        - setProperty()
        - QML signals/slots
        - Connections in QML to C++/Python slots
    """

    QML_FILE: Path = ""  # Derived classes MUST set this

    def __init__(
        self,
        config: OverlaysConfig,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
    ):
        assert self.QML_FILE, "Derived classes must define QML_FILE"

        QObject.__init__(self)
        self._engine = QQmlApplicationEngine()
        self._root: Optional[QQuickWindow] = None
        self._fade_anim = None
        self._drag_pos: Optional[QPoint] = None

        self._frame_timer = QTimer(self)
        self._frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._frame_timer.timeout.connect(self._on_frame)

        super().__init__(
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
        )
        logger.debug(f"{self.OVERLAY_ID} initialized. Path={self.QML_FILE}. "
                     f"exists={self.QML_FILE.is_file()}")

    # ----------------------------------------------------------------------
    # Window + QML Setup
    # ----------------------------------------------------------------------
    @override
    def _setup_window(self):
        """Load QML and extract the root QQuickWindow."""

        qml_path = self.QML_FILE.resolve()
        self._engine.load(QUrl.fromLocalFile(str(qml_path)))

        if not self._engine.rootObjects():
            raise RuntimeError(f"Failed to load QML file: {qml_path}")

        root = self._engine.rootObjects()[0]
        if not isinstance(root, QQuickWindow):
            raise TypeError(
                f"Root QML object must be a Window; got {type(root).__name__}"
            )

        self._root = root
        self._root.installEventFilter(self)
        self._root.setProperty("scaleFactor", self.scale_factor)

        super()._setup_window()
        self.update_window_flags()
        self._root.setVisible(True)
        self._frame_timer.start(16) # 60 Hz default; TODO: make configurable later

    # ----------------------------------------------------------------------
    # Abstract method implementations
    # ----------------------------------------------------------------------
    def set_window_title(self, title: str):
        self._root.setTitle(title)

    def set_window_icon(self, icon: QIcon):
        self._root.setIcon(icon)

    def build_ui(self):
        raise NotImplementedError

    @override
    def apply_config(self):
        self._root.setPosition(self.config.x, self.config.y)
        self.set_opacity(self.opacity)

    @override
    def update_window_flags(self):

        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        if self.windowed_overlay:
            flags |= Qt.WindowType.Window
        else:
            flags |= Qt.WindowType.Tool
            if self.locked:
                flags |= Qt.WindowType.WindowTransparentForInput

        self._root.setFlags(flags)

    @override
    def set_opacity(self, opacity: int):
        self._root.setOpacity(opacity / 100.0)

    @override
    def set_locked_state(self, locked: bool):
        self.locked = locked
        self.update_window_flags()

    @override
    def set_ui_scale(self, ui_scale: float):
        """
        Update the UI scale factor at runtime.

        This updates the scaleFactor property in QML if it exists,
        allowing the QML UI to dynamically resize all scaled elements.

        Args:
            ui_scale: New scale factor (e.g., 1.0, 1.5, 2.0)
        """
        self.scale_factor = ui_scale

        if self._root:
            # Check if the QML root has a scaleFactor property
            if self._root.property("scaleFactor") is not None:
                self._root.setProperty("scaleFactor", ui_scale)
                self.logger.debug(f"{self.OVERLAY_ID} | UI scale updated to {ui_scale}")
            else:
                self.logger.warning(
                    f"{self.OVERLAY_ID} | QML root does not have 'scaleFactor' property. "
                    "Add 'property real scaleFactor: 1.0' to your QML Window."
                )
        else:
            self.logger.warning(f"{self.OVERLAY_ID} | Cannot set UI scale - root window not initialized")

    @override
    def animate_fade(self, show: bool):

        start, end = (0, 1) if show else (1, 0)

        anim = QPropertyAnimation(self._root, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(start)
        anim.setEndValue(end)

        if not show:
            anim.finished.connect(lambda: self._root.setVisible(False))
        else:
            self._root.setOpacity(0)
            self._root.setVisible(True)

        self._fade_anim = anim
        anim.start()

    @override
    def toggle_visibility(self):

        if self._root.isVisible():
            self.animate_fade(False)
        else:
            self.animate_fade(True)

    @override
    def get_window_info(self) -> OverlaysConfig:
        pos = self._root.position()
        return OverlaysConfig(x=pos.x(), y=pos.y())

    @override
    def set_window_position(self, config: OverlaysConfig):
        self.config = config
        self._root.setPosition(config.x, config.y)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:

        if obj is self._root and not self.locked:

            if event.type() == QEvent.Type.MouseButtonPress:
                mouse_event: QMouseEvent = event
                if mouse_event.button() == Qt.MouseButton.LeftButton:
                    self._drag_pos = (
                        mouse_event.globalPosition().toPoint()
                        - self._root.position()
                    )
                    return True

            elif event.type() == QEvent.Type.MouseMove:
                mouse_event: QMouseEvent = event
                if (
                    mouse_event.buttons() & Qt.MouseButton.LeftButton
                    and self._drag_pos
                ):
                    self._root.setPosition(
                        mouse_event.globalPosition().toPoint() - self._drag_pos
                    )
                    return True

            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_pos = None
                return True

        return super().eventFilter(obj, event)

    # ----------------------------------------------------------------------
    # Rendering methods
    # ----------------------------------------------------------------------
    def _on_frame(self):
        """
        Fixed-rate render tick for QML overlays.
        Derived classes may override _render_frame().
        """
        if not self._root or not self._root.isVisible():
            return

        self.render_frame()

    def render_frame(self):
        """Derived classes must implement this method."""
        raise NotImplementedError
