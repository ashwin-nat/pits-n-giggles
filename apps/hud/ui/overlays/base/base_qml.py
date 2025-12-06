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
from typing import Optional, override

from PySide6.QtCore import QPropertyAnimation, Qt, QUrl, QObject
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from apps.hud.ui.infra.config import OverlaysConfig

from .base import BaseOverlay

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
        overlay_id: str,
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

        super().__init__(
            overlay_id,
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
        )

        logger.debug(f"{overlay_id} | BaseOverlayQML initialized")

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
        super()._setup_window()
        self.update_window_flags()
        self._root.setVisible(True)

    # ----------------------------------------------------------------------
    # Abstract method implementations
    # ----------------------------------------------------------------------
    def set_window_title(self, title: str):
        self._root.setTitle(title)

    def set_window_icon(self, icon: QIcon):
        self._root.setIcon(icon)

    def build_ui(self):
        raise NotImplementedError

    def rebuild_ui(self):
        """Reloads the QML file entirely when scale factor changes."""

        qml_path = self.QML_FILE.resolve()
        self.logger.debug(f"{self.overlay_id} | Rebuilding QML UI ({qml_path})")

        self._engine.clearComponentCache()
        self._engine.load(QUrl.fromLocalFile(str(qml_path)))

        if not self._engine.rootObjects():
            raise RuntimeError("Failed to rebuild QML UI")

        self._root = self._engine.rootObjects()[0]
        self.update_window_flags()
        self.apply_config()

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
        self.opacity = opacity
        self._root.setOpacity(opacity / 100.0)

    @override
    def set_locked_state(self, locked: bool):
        self.locked = locked
        self.update_window_flags()

    @override
    def set_ui_scale(self, ui_scale):
        pass

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
