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
from typing import override

from PySide6.QtCore import QPropertyAnimation, Qt
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QWidget

from apps.hud.ui.infra.config import OverlaysConfig

from .base import BaseOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlayWidget(BaseOverlay, QWidget):
    """
    Base class for all QWidget-based overlays.

    This class provides the full QWidget implementation of the UI/windowing
    behaviors expected by `BaseOverlay`. It acts as the concrete backend for
    overlays that render their UI using Qt Widgets. Any overlay that uses
    QWidget layouts, labels, and other standard widget components should derive
    from this class.

    --------------------------------------------------------------------------
    WHAT THIS CLASS IMPLEMENTS
    --------------------------------------------------------------------------
    - Construction of a top-level QWidget window (frameless, always-on-top,
      optionally click-through depending on locked/unlocked state).
    - Applying window flags and updating them when the overlay's locked state
      changes.
    - Window sizing via `adjustSize()` after UI construction or rebuilds.
    - Position and opacity management (`move()`, `setWindowOpacity()`).
    - Fade-in / fade-out animation using `QPropertyAnimation` on the window
      opacity.
    - Mouse-based dragging when unlocked (left-drag to reposition the overlay).
    - Layout teardown and recreation on scale-factor changes (`rebuild_ui()`).
    - Standard QWidget geometry/visibility methods (`geometry`, `isVisible`,
      `show`, `hide`).

    --------------------------------------------------------------------------
    WHAT DERIVED CLASSES MUST IMPLEMENT
    --------------------------------------------------------------------------
    - build_ui(self):
        Construct all widget children and layouts that make up the overlay's
        visible UI. This is called on startup and any time the overlay is
        rebuilt (e.g., when the scale factor changes).

    Derived overlays do NOT need to implement window setup, window flags,
    geometry logic, positioning, dragging, opacity, or animation—these are
    fully handled here.
    """
    def __init__(self,
                 config: OverlaysConfig,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool):

        QWidget.__init__(self)
        BaseOverlay.__init__(
            self,
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
        )
        self.adjustSize()

        logger.debug(f"{self.OVERLAY_ID} | BaseOverlay initialized")

        self._drag_pos = None
        self._fade_anim = None

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------
    @override
    def _setup_window(self):
        super()._setup_window()

        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")
        self.update_window_flags()
        self.adjustSize()

    def set_window_title(self, title: str):
        self.setWindowTitle(title)

    def set_window_icon(self, icon: QIcon):
        self.setWindowIcon(icon)

    # ------------------------------------------------------------------
    # UI build + rebuild
    # ------------------------------------------------------------------
    @override
    def apply_config(self):
        self.move(self.config.x, self.config.y)
        self.set_opacity(self.opacity)

    def build_ui(self):
        raise NotImplementedError

    def rebuild_ui(self):
        """
        Completely rebuild the overlay UI.

        This removes:
            - All child widgets (QLabel, QPushButton, QStackedWidget pages, etc.)
            - The existing layout object attached to this overlay

        Why this is required:
            Qt does NOT allow calling setLayout() on a widget that already has a layout.
            Our cleanup removes child widgets, but layouts are NOT widgets, so they remain
            attached unless removed explicitly. Without removing the old layout, the new
            layout assigned inside build_ui() would be ignored, leaving the window blank.

        Steps performed:
            1. Detach and delete all child widgets using setParent(None) + deleteLater().
            2. Detach and delete the existing layout via the QWidget().setLayout(...) idiom.
            3. Call build_ui() to construct a fresh widget tree.

        This ensures the overlay fully regenerates correctly (e.g., after scale changes).
        """

        # 1. Remove all child widgets (covers entire widget tree)
        for w in self.findChildren(QWidget):
            self.logger.debug(f"{self.OVERLAY_ID} | Cleaning widget: {w.__class__.__name__}")
            w.setParent(None)
            w.deleteLater()

        # 2. Remove the existing layout if present.
        old_layout = self.layout()
        if old_layout is not None:
            # Reparenting the layout to a temporary QWidget forces Qt to delete it.
            QWidget().setLayout(old_layout)

        # 3. Rebuild UI fresh
        self.build_ui()
        self.update_window_flags()

    @override
    def get_window_info(self) -> OverlaysConfig:
        """Return current geometry as an OverlaysConfig."""
        geo = self.geometry()
        return OverlaysConfig(x=geo.x(), y=geo.y())

    @override
    def set_window_position(self, config: OverlaysConfig):
        self.move(config.x, config.y)
        self.config = config

    @override
    def toggle_visibility(self):

        self.logger.debug(f'{self.OVERLAY_ID} | Toggling visibility')
        if self.isVisible():
            self.logger.debug(f'{self.OVERLAY_ID} | Fading out overlay')
            self.animate_fade(show=False)
        else:
            self.logger.debug(f'{self.OVERLAY_ID} | Fading in overlay')
            self.animate_fade(show=True)

    # ------------------------------------------------------------------
    # Window flag logic
    # ------------------------------------------------------------------
    @override
    def update_window_flags(self):
        """Refresh window flags based on locked state."""
        flags = (
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        if self.windowed_overlay:
            # Standalone OBS-capturable windows always behave like real top-level windows
            flags |= Qt.WindowType.Window
        else:
            flags |= Qt.WindowType.Tool

            if self.locked:
                flags |= Qt.WindowType.WindowTransparentForInput
            else:
                # Interactive behavior for unlocked state
                flags |= (
                    Qt.WindowType.Window |
                    Qt.WindowType.CustomizeWindowHint |
                    Qt.WindowType.MSWindowsFixedSizeDialogHint
                )

        self.setWindowFlags(flags)
        self.show()

    # ------------------------------------------------------------------
    # Opacity / Locked State
    # ------------------------------------------------------------------
    @override
    def set_opacity(self, opacity: int):
        self.opacity = opacity
        self.setWindowOpacity(opacity / 100.0)

    @override
    def set_locked_state(self, locked: bool):
        self.locked = locked
        self.update_window_flags()

    @override
    def set_ui_scale(self, ui_scale):
        self.scale_factor = ui_scale
        self.rebuild_ui()

    # ------------------------------------------------------------------
    # Fade
    # ------------------------------------------------------------------
    @override
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
    # Dragging
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        if not self.locked and event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.locked and event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _event: QMouseEvent):
        self._drag_pos = None
