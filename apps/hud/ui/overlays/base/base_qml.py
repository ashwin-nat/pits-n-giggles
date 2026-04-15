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
from time import perf_counter_ns
from typing import Optional, TypeVar, final, override

from PySide6.QtCore import (QEvent, QMetaObject, QObject, QPoint, QSize,
                            QPropertyAnimation, Qt, QTimer, QUrl, Slot)
from PySide6.QtCore import Q_ARG
from PySide6.QtGui import QCursor, QIcon, QMouseEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from apps.hud.ui.infra.hf_types import HighFreqBase
from lib.config import OverlayPosition

from .base import BaseOverlay

# -------------------------------------- TYPES -------------------------------------------------------------------------

HighFreqObjType = TypeVar("HighFreqObjType", bound=HighFreqBase)
_UNSET = object()  # sentinel for absent QML property cache entries

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

    _RESIZE_MIN_SCALE = 0.1   # minimum allowed scale factor during resize
    _RESIZE_MIN_WIDTH = 50    # minimum pixel width used to clamp raw_w before scale computation

    _CORNER_CURSORS = {
        Qt.Corner.TopLeftCorner:     Qt.CursorShape.SizeFDiagCursor,
        Qt.Corner.TopRightCorner:    Qt.CursorShape.SizeBDiagCursor,
        Qt.Corner.BottomLeftCorner:  Qt.CursorShape.SizeBDiagCursor,
        Qt.Corner.BottomRightCorner: Qt.CursorShape.SizeFDiagCursor,
    }

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
        refresh_interval_ms: Optional[int],
    ):
        """Initialize QML overlay.

        Args:
            config (OverlayPosition): Overlay config
            logger (logging.Logger): Logger object
            locked (bool): Locked state
            opacity (int): Window opacity
            scale_factor (float): UI Scale factor (multiplier)
            windowed_overlay (bool): Windowed overlay
            refresh_interval_ms (Optional[int]): Refresh interval. If not specified, re-paint timer is disabled.
                    The overlay is responsible to repaint itself (preferably on telemetry update)
        """
        assert self.QML_FILE, "Derived classes must define QML_FILE"
        assert isinstance(self.QML_FILE, Path), "QML_FILE must be a pathlib.Path"
        assert self.QML_FILE.is_file(), f"QML_FILE does not exist or is not a file: {self.QML_FILE}"

        QObject.__init__(self)
        self._engine = QQmlApplicationEngine()
        self._root: Optional[QQuickWindow] = None
        self._unlock_overlay: Optional[QQuickItem] = None
        self._fade_anim = None
        self._drag_pos: Optional[QPoint] = None
        self._qml_props: dict = {}

        self._refresh_interval_ms = refresh_interval_ms
        if refresh_interval_ms:
            self._fps = max(1, round(1000 / self._refresh_interval_ms))
        else:
            self._fps = 0
        self._frame_timer = QTimer(self)
        self._frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._frame_timer.timeout.connect(self._on_frame)
        self._frame_active: bool = False
        self._resize_origin: Optional[QPoint] = None
        self._resize_origin_size: Optional[QSize] = None
        self._resize_origin_pos: Optional[QPoint] = None
        self._resize_corner: Optional[Qt.Corner] = None
        self._resize_origin_scale: float = 1.0

        super().__init__(
            config,
            logger,
            locked,
            opacity,
            scale_factor,
            windowed_overlay,
        )
        logger.debug("%s initialized. Path=%s. exists=%s",
                     self.OVERLAY_ID, self.QML_FILE, self.QML_FILE.is_file())

    # ----------------------------------------------------------------------
    # Window + QML Setup
    # ----------------------------------------------------------------------
    @override
    def _setup_window(self):
        """Load QML and extract the root QQuickWindow."""

        qml_logger = QmlLogger(self.logger, self.OVERLAY_ID)
        self._engine.rootContext().setContextProperty("Log", qml_logger)

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
        self._create_unlock_overlay()
        self.update_window_flags()
        self._root.setVisible(True)
        if self._refresh_interval_ms is not None:
            self._frame_timer.start(self._refresh_interval_ms)

    @final
    def build_ui(self):
        pass # QML based overlays dont need this

    # ----------------------------------------------------------------------
    # Abstract method implementations
    # ----------------------------------------------------------------------
    def set_window_title(self, title: str):
        self._root.setTitle(title)

    def set_window_icon(self, icon: QIcon):
        self._root.setIcon(icon)

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
        self._update_unlock_overlay()

    def _create_unlock_overlay(self):
        """Create the unlock-mode border+handles overlay once after the root window is ready.
        Starts hidden; visibility is toggled by _update_unlock_overlay()."""
        qml_path = (Path(__file__).parent / "OverlayBorder.qml").resolve()
        component = QQmlComponent(self._engine, QUrl.fromLocalFile(str(qml_path)))
        obj = component.create()
        if obj is None:
            self.logger.error(
                "%s | Failed to create UnlockOverlay: %s",
                self.OVERLAY_ID, component.errorString(),
            )
            return
        if not isinstance(obj, QQuickItem):
            self.logger.error("%s | UnlockOverlay root is not a QQuickItem", self.OVERLAY_ID)
            return
        obj.setParent(self._root)
        obj.setParentItem(self._root.contentItem())
        obj.setZ(9999)
        obj.setVisible(False)
        self._unlock_overlay = obj

    def _update_unlock_overlay(self):
        """Show or hide the unlock overlay based on locked state."""
        if self._unlock_overlay is None:
            return
        self._unlock_overlay.setVisible(not self.locked)

    @override
    def set_opacity(self, opacity: int):
        self._root.setOpacity(opacity / 100.0)

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
                self.logger.debug("%s | UI scale updated to %s", self.OVERLAY_ID, ui_scale)
            else:
                self.logger.warning(
                    f"{self.OVERLAY_ID} | QML root does not have 'scaleFactor' property. "
                    "Add 'property real scaleFactor: 1.0' to your QML Window."
                )
        else:
            self.logger.warning("%s | Cannot set UI scale - root window not initialized", self.OVERLAY_ID)

    def animate_fade(self, show: bool):

        target_opacity = self.opacity / 100.0
        start, end = (0, target_opacity) if show else (target_opacity, 0)

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
    def set_visibility(self, visible: bool):
        self.animate_fade(visible)

    @override
    def get_window_info(self) -> OverlayPosition:
        pos = self._root.position()
        return OverlayPosition(x=pos.x(), y=pos.y(), scale_factor=self.scale_factor)

    @override
    def set_window_position(self, config: OverlayPosition):
        self.config = config
        self._root.setPosition(config.x, config.y)

    @override
    def get_visibility(self) -> bool:
        return self._root.isVisible()

    def _get_resize_corner_px(self) -> int:
        """Return the corner handle size in logical pixels.

        Reads the value from the UnlockOverlay QML item (single source of truth)
        so the hit area always matches the visual handle size.  Falls back to 18
        if the overlay is not yet created or the property is unavailable.
        """
        if self._unlock_overlay is not None:
            val = self._unlock_overlay.property("handleSize")
            if isinstance(val, int) and val > 0:
                return val
        return 18  # fallback – matches OverlayBorder.qml default

    def _corner_at(self, local_pos: QPoint) -> Optional[Qt.Corner]:
        """Return the nearest corner if local_pos is within the resize zone, else None."""
        w = self._root.width()
        h = self._root.height()
        r = self._get_resize_corner_px()
        x, y = local_pos.x(), local_pos.y()
        if x <= r and y <= r:
            return Qt.Corner.TopLeftCorner
        if x >= w - r and y <= r:
            return Qt.Corner.TopRightCorner
        if x <= r and y >= h - r:
            return Qt.Corner.BottomLeftCorner
        if x >= w - r and y >= h - r:
            return Qt.Corner.BottomRightCorner
        return None

    def _on_mouse_press(self, event: QMouseEvent) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        local = event.position().toPoint()
        corner = self._corner_at(local)
        if corner is not None:
            self._resize_origin = event.globalPosition().toPoint()
            self._resize_origin_size = QSize(self._root.width(), self._root.height())
            self._resize_corner = corner
            self._resize_origin_pos = self._root.position()
            self._resize_origin_scale = self.scale_factor
            self._drag_pos = None
        else:
            self._drag_pos = event.globalPosition().toPoint() - self._root.position()
            self._resize_origin = None
        return True

    def _on_mouse_move(self, event: QMouseEvent) -> bool:
        global_pos = event.globalPosition().toPoint()
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._resize_origin is not None:
                return self._on_resize_drag(global_pos)
            if self._drag_pos is not None:
                self._root.setPosition(global_pos - self._drag_pos)
                return True
        else:
            self._on_hover_cursor(event.position().toPoint())
        return False

    def _on_resize_drag(self, global_pos: QPoint) -> bool:
        delta = global_pos - self._resize_origin
        orig_w = self._resize_origin_size.width()
        if orig_w <= 0:
            # Guard against invalid or zero width to avoid division-by-zero
            # and extreme scaling in edge cases (e.g. initial layout).
            return False
        orig_h = self._resize_origin_size.height()
        orig_pos = self._resize_origin_pos
        corner = self._resize_corner

        # Aspect ratio is preserved by QML, so drive scale from width only.
        if corner in (Qt.Corner.TopLeftCorner, Qt.Corner.BottomLeftCorner):
            raw_w = orig_w - delta.x()
        else:
            raw_w = orig_w + delta.x()

        new_scale = max(
            self._RESIZE_MIN_SCALE,
            self._resize_origin_scale * (max(self._RESIZE_MIN_WIDTH, raw_w) / orig_w),
        )
        scale_ratio = new_scale / self._resize_origin_scale
        new_w = round(orig_w * scale_ratio)
        new_h = round(orig_h * scale_ratio)

        # Anchor the stationary corner by adjusting window position.
        if corner == Qt.Corner.TopLeftCorner:
            self._root.setPosition(QPoint(
                orig_pos.x() + (orig_w - new_w),
                orig_pos.y() + (orig_h - new_h),
            ))
        elif corner == Qt.Corner.TopRightCorner:
            self._root.setPosition(QPoint(
                orig_pos.x(),
                orig_pos.y() + (orig_h - new_h),
            ))
        elif corner == Qt.Corner.BottomLeftCorner:
            self._root.setPosition(QPoint(
                orig_pos.x() + (orig_w - new_w),
                orig_pos.y(),
            ))
        # BottomRight: position unchanged

        self.set_ui_scale(new_scale)
        return True

    def _on_hover_cursor(self, local: QPoint) -> None:
        corner = self._corner_at(local)
        if corner is not None:
            self._root.setCursor(QCursor(self._CORNER_CURSORS[corner]))
        else:
            self._root.unsetCursor()

    def _on_mouse_release(self) -> bool:
        self._drag_pos = None
        self._resize_origin = None
        return True

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._root and not self.locked:
            t = event.type()
            if t == QEvent.Type.MouseButtonPress:
                return self._on_mouse_press(event)
            if t == QEvent.Type.MouseMove:
                return self._on_mouse_move(event)
            if t == QEvent.Type.MouseButtonRelease:
                return self._on_mouse_release()
        return super().eventFilter(obj, event)

    # ----------------------------------------------------------------------
    # Rendering methods
    # ----------------------------------------------------------------------
    def _on_frame(self):
        """
        Fixed-rate render tick for QML overlays.
        Derived classes may override _render_frame().
        """
        if not self._root:
            self._frame_active = False
            self._stats.track_event("__FRAMES__", "__DROPPED_NO_ROOT__")
            return

        if not self.get_visibility():
            self._frame_active = False
            self._stats.track_event("__FRAMES__", "__DROPPED_HIDDEN__")
            return

        # First frame after becoming visible — reset timing baseline so the
        # hidden gap is not counted as a missed/late frame.
        if not self._frame_active:
            self._reset_frame_timing()
            self._frame_active = True

        self.render_frame()
        self._clear_hf_pending()
        assert self._refresh_interval_ms
        assert self._fps
        self._stats.track_frame_render("__FRAMES__", "__FRAME__", perf_counter_ns(), self._fps)

    def _reset_frame_timing(self) -> None:
        """Reset the frame timing baseline so hidden gaps are excluded from metrics."""
        self._stats.reset_frame_timing("__FRAMES__", "__FRAME__")

    def invalidate_qml_cache(self, *names: str) -> None:
        """Remove one or more property names from the cache so the next
        set_qml_property call always pushes the value to QML regardless of
        whether it matches the previously cached value."""
        for name in names:
            self._qml_props.pop(name, None)

    def set_qml_property(self, name: str, value) -> None:
        """Set a property on the QML root object.

        Silently does nothing if the root is not yet initialized or if the
        property already holds the same value. Uses a local dict to track
        last-set values to avoid the cost of reading back through the Qt
        meta-object system.
        """
        if self._root is None:
            return
        if self._qml_props.get(name, _UNSET) == value:
            return
        self._qml_props[name] = value
        self._root.setProperty(name, value)

    @property
    def root(self) -> Optional[QQuickWindow]:
        """The root QML window. Available after _setup_window() completes."""
        return self._root

    def on_event(self, cmd_name: str, requires_root: bool = True):
        """Register a command handler, optionally guarded by root availability.

        Args:
            cmd_name: The event/command name to handle.
            requires_root: When True (default), the handler is silently dropped
                and counted under ``__DROPPED_NO_ROOT__`` if the QML root window
                is not yet initialised. Set to False for handlers that must run
                even before the window is ready.
        """
        def decorator(func):
            if requires_root:
                def wrapper(data, _cmd=cmd_name):
                    if not self._root:
                        self._stats.track_event("__DROPPED_NO_ROOT__", _cmd)
                        return None
                    return func(data)
                self._command_handlers[cmd_name] = wrapper
            else:
                self._command_handlers[cmd_name] = func
            return func
        return decorator

    def invoke_qml_method(self, method: str, *args) -> None:
        """Invoke a QML method on the root window with QVariant arguments.

        All positional args are forwarded as ``QVariant`` via a queued
        connection, matching the standard pattern used across QML overlays.
        """
        QMetaObject.invokeMethod(
            self._root,
            method,
            Qt.ConnectionType.QueuedConnection,
            *(Q_ARG("QVariant", a) for a in args),
        )

    def _track_frame(self) -> None:
        self._stats.track_event("__FRAMES__", "__RENDERED__")

    def render_frame(self):
        """Derived classes must implement this method."""
        raise NotImplementedError

class QmlLogger(QObject):
    def __init__(self, logger: logging.Logger, oid: str):
        super().__init__()
        self._logger = logger
        self._oid = oid

    @Slot(str)
    def debug(self, msg):
        self._logger.debug("%s | %s", self._oid, msg)

    @Slot(str)
    def info(self, msg):
        self._logger.info("%s | %s", self._oid, msg)

    @Slot(str)
    def warn(self, msg):
        self._logger.warning("%s | %s", self._oid, msg)

    @Slot(str)
    def error(self, msg):
        self._logger.error("%s | %s", self._oid, msg)
