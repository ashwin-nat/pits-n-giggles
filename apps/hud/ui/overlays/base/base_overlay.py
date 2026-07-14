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
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import (TYPE_CHECKING, Any, Callable, Dict, Optional, Type,
                    TypeVar)

from PySide6.QtCore import (Q_ARG, QEvent, QMetaObject, QObject, QPoint,
                            QPropertyAnimation, QSize, Qt, QTimer, QUrl,
                            Signal, Slot)
from PySide6.QtGui import QCursor, QIcon, QMouseEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from apps.hud.ui.infra.hf_types import HighFreqBase
from lib.assets_loader import load_icon
from lib.config import OverlayPosition
from meta.meta import APP_NAME_SNAKE

from .qml_bridge import QmlBridge

if TYPE_CHECKING:
    from apps.hud.ui.infra.window_mgr import WindowManager

# -------------------------------------- TYPES -------------------------------------------------------------------------

OverlayRequestHandler = Callable[[Dict[str, Any]], str] # Takes dict arg, returns str (serialised JSON)

HighFreqObjType = TypeVar("HighFreqObjType", bound=HighFreqBase)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlay(QmlBridge, QObject):
    """
    Base class for all QML overlay windows.

    Owns the QML window (QQuickWindow) and the process-facing transport: every
    overlay gets the command/request dispatch infrastructure, the high-frequency
    data channel, and the window lifecycle in one place.

    --------------------------------------------------------------------------
    WHAT THIS CLASS IMPLEMENTS
    --------------------------------------------------------------------------
    - Overlay identity, configuration, and runtime state
    - Command/request dispatch (via QmlBridge.on_event / dispatch_event)
    - Default commands: toggling visibility, locked state, opacity, window
      config, telemetry-active gating, get_window_info, get_window_stats
    - High-frequency data subscription, caching, and loss accounting
    - Loading QML from disk using QQmlApplicationEngine
    - Ownership of the root QML window (QQuickWindow)
    - Applying window flags (always-on-top, frameless, tool vs full window)
    - Position & opacity management via QQuickWindow
    - Fade-in/fade-out via QPropertyAnimation bound to QQuickWindow.opacity
    - Allowing locked/unlocked (click-through) behavior via flags
    - Windowed Overlay Mode (OBS capture)
    - Optional fixed-rate render tick (refresh_interval_ms constructor arg);
      event-driven overlays pass None and repaint on telemetry updates

    --------------------------------------------------------------------------
    WHAT DERIVED CLASSES MUST PROVIDE
    --------------------------------------------------------------------------
    - OVERLAY_ID class attribute
    - A QML file path via the QML_FILE class attribute
    - QML should expose a root Window {} containing `property real scaleFactor`
    - render_frame() if a refresh interval is used

    Lifecycle hooks (override in leaf classes):
        - pre_setup()   - before the QML window is created
        - post_setup()  - after the QML window is created

    """

    response_signal = Signal(str, object)   # request_type, response_data
    OVERLAY_ID: str = ""
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

        QmlBridge.__init__(self)
        QObject.__init__(self)

        self._engine = QQmlApplicationEngine()
        self._root: Optional[QQuickWindow] = None
        self._unlock_overlay: Optional[QQuickItem] = None
        self._fade_anim = None
        self._drag_pos: Optional[QPoint] = None

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

        assert self.OVERLAY_ID

        self.windowed_overlay = windowed_overlay
        self.config = config
        self.locked = locked
        self.logger = logger
        self.opacity = opacity
        self.scale_factor = scale_factor
        self.telemetry_active = True

        self._request_handlers: Dict[str, OverlayRequestHandler] = {}
        self._hf_subscriptions: set[str] = set()
        self._window_manager: Optional["WindowManager"] = None  # set via set_window_manager() during registration
        self._user_hidden: bool = False  # True when user explicitly hid this overlay

        # Create the actual window
        self.pre_setup()
        self._setup_window()
        self.post_setup()
        self.apply_config()

        # Register default handlers
        self._register_default_handlers()

        logger.debug("%s initialized. Path=%s. "
                     "exists=%s", self.OVERLAY_ID, self.QML_FILE, self.QML_FILE.is_file())

    @property
    def is_animation_overlay(self) -> bool:
        return self._refresh_interval_ms is not None

    # ------------------------------------------------------------------
    # QmlBridge: _qml_target implementation
    # ------------------------------------------------------------------
    @property
    def _qml_target(self) -> Optional[QQuickWindow]:
        return self._root

    @property
    def qml_engine(self) -> QQmlApplicationEngine:
        """The QML engine for this overlay."""
        return self._engine

    @property
    def root(self) -> Optional[QQuickWindow]:
        """The root QML window. Available after _setup_window() completes."""
        return self._root

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def pre_setup(self):
        """Hook called before _setup_window(). Override in leaf classes with @final.

        Called from base __init__ before subclass __init__ has run - overrides must not
        depend on any subclass-initialized state.
        """

    def post_setup(self):
        """Hook called after _setup_window() completes. Override in leaf classes with @final."""

    # ------------------------------------------------------------------
    # Window + QML Setup
    # ------------------------------------------------------------------
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

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME_SNAKE)
        self.set_window_title(self.OVERLAY_ID)
        self.set_window_icon(load_icon(Path("assets") / "logo.png",
                                     debug_log_printer=self.logger.debug,
                                     error_log_printer=self.logger.error))

        self._create_unlock_overlay()
        self.update_window_flags()
        self._root.setVisible(True)
        if self._refresh_interval_ms is not None:
            self._frame_timer.start(self._refresh_interval_ms)
            # frameSwapped fires on the render thread; QueuedConnection marshals the
            # handler onto the GUI thread so the stat object is only ever touched there.
            self._root.frameSwapped.connect(self._on_frame_swapped, Qt.ConnectionType.QueuedConnection)

    # ------------------------------------------------------------------
    # Common handlers
    # ------------------------------------------------------------------

    def set_locked_state(self, locked: bool):
        """Common handler for setting locked state."""
        self.locked = locked
        self.update_window_flags()

        if self.locked and not self.telemetry_active:
            self.logger.debug("%s locking overlay. But hiding it since telemetry is not active", self.OVERLAY_ID)
            self.set_visibility(False)

    def toggle_visibility(self):
        """Common handler for toggling visibility."""
        self.logger.debug('%s | Toggling visibility', self.OVERLAY_ID)
        if self.get_visibility():
            self.logger.debug('%s | Fading out overlay', self.OVERLAY_ID)
            self.set_visibility(False)
            self._user_hidden = True
        else:
            self.logger.debug('%s | Fading in overlay', self.OVERLAY_ID)
            self.set_visibility(True)
            self._user_hidden = False

    def set_telemetry_active(self, active: bool):
        """Common handler for setting telemetry active state."""
        self.logger.debug("%s set_telemetry_active: %s", self.OVERLAY_ID, active)
        self.telemetry_active = active

        if not self.locked:
            # In unlocked mode. user is probably editing the overlay.
            # Hence no-op
            return

        if active:
            if not self._user_hidden:
                self.set_visibility(True)
        else:
            self.set_visibility(False)

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------
    def set_window_title(self, title: str):
        self._root.setTitle(title)

    def set_window_icon(self, icon: QIcon):
        self._root.setIcon(icon)

    def apply_config(self):
        self._root.setPosition(self.config.x, self.config.y)
        self.set_opacity(self.opacity)

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

    def set_opacity(self, opacity: int):
        self._root.setOpacity(opacity / 100.0)

    def set_ui_scale(self, ui_scale: float):
        """Update the UI scale factor at runtime."""
        self.scale_factor = ui_scale

        if self._root:
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
        if self._fade_anim is not None:
            self._fade_anim.stop()

        target_opacity = self.opacity / 100.0
        start, end = (0, target_opacity) if show else (target_opacity, 0)

        anim = QPropertyAnimation(self._root, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(start)
        anim.setEndValue(end)

        if not show:
            anim.finished.connect(self._on_fade_out_finished)
        else:
            self._root.setOpacity(0)
            self._root.setVisible(True)
            self._start_frame_timer()
            self._replay_cached_state()

        self._fade_anim = anim
        anim.start()

    def _on_fade_out_finished(self):
        """Fade-out completed: hide the window and stop the render tick."""
        self._root.setVisible(False)
        self._stop_frame_timer()

    def _replay_cached_state(self) -> None:
        """Redeliver the latest known snapshot for every handled topic on becoming visible.

        While hidden, non-high-priority commands are dropped in _handle_cmd, so a state
        topic's mailbox can advance well past what this overlay last processed. Without this,
        a freshly shown overlay displays whatever it last rendered until the next broadcast
        arrives, which can be seconds away. replay_state_topic() no-ops for anything that
        isn't a state topic.
        """
        if self._window_manager is None:
            return
        for cmd in self._handlers:
            data = self._window_manager.replay_state_topic(self.OVERLAY_ID, cmd)
            if data is None:
                continue
            try:
                self.dispatch_event(cmd, data["__payload__"])
            except Exception:  # pylint: disable=broad-exception-caught
                self.logger.exception("%s | Error replaying cached state for '%s'", self.OVERLAY_ID, cmd)

    def _start_frame_timer(self) -> None:
        if self._refresh_interval_ms is not None and not self._frame_timer.isActive():
            self._frame_timer.start(self._refresh_interval_ms)

    def _stop_frame_timer(self) -> None:
        if self._frame_timer.isActive():
            self._frame_timer.stop()
        self._frame_active = False

    def set_visibility(self, visible: bool):
        self.animate_fade(visible)

    def get_window_info(self) -> OverlayPosition:
        pos = self._root.position()
        return OverlayPosition(x=pos.x(), y=pos.y(), scale_factor=self.scale_factor)

    def set_window_position(self, config: OverlayPosition):
        self.config = config
        self._root.setPosition(config.x, config.y)

    def get_visibility(self) -> bool:
        return self._root.isVisible()

    # ------------------------------------------------------------------
    # Drag / resize handling (unlocked mode)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Rendering methods
    # ------------------------------------------------------------------
    def _on_frame(self):
        """Fixed-rate render tick. Derived classes implement render_frame()."""
        if not self._root:
            self._frame_active = False
            self._stats.track_event("__FRAMES_PRODUCER__", "__DROPPED_NO_ROOT__")
            return

        if not self.get_visibility():
            self._frame_active = False
            self._stats.track_event("__FRAMES_PRODUCER__", "__DROPPED_HIDDEN__")
            return

        # First frame after becoming visible - reset timing baseline so the
        # hidden gap is not counted as a missed/late frame.
        if not self._frame_active:
            self._reset_frame_timing()
            self._frame_active = True

        self.render_frame()
        assert self._refresh_interval_ms
        assert self._fps
        self._stats.track_frame_render("__FRAMES_PRODUCER__", "__FRAME__", perf_counter_ns(), self._fps)

    def _reset_frame_timing(self) -> None:
        """Reset the frame timing baseline so hidden gaps are excluded from metrics."""
        self._stats.reset_frame_timing("__FRAMES_PRODUCER__", "__FRAME__")

    def _on_frame_swapped(self) -> None:
        """Passive record of an actually-presented frame.

        Observes; never drives. Unlike the QML FrameAnimation this replaces, connecting
        here forces nothing - frameSwapped only fires when a frame would have been
        presented anyway, so "__FRAMES_RENDERED__" reflects the overlay's real repaint
        cadence instead of the monitor refresh rate.
        """
        self._stats.track_frame_render("__FRAMES_RENDERED__", "__FRAME__", perf_counter_ns(), self._fps)

    def render_frame(self):
        """Derived classes must implement this method if a refresh interval is used."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # QML method invocation
    # ------------------------------------------------------------------
    def invoke_qml_method(self, method: str, *args) -> None:
        """Invoke a QML method on the root window with QVariant arguments."""
        self._stats.track_event("__QML_METHOD_CALLS__", method)
        QMetaObject.invokeMethod(
            self._root,
            method,
            Qt.ConnectionType.AutoConnection,
            *(Q_ARG("QVariant", a) for a in args),
        )

    # ------------------------------------------------------------------
    # Request handler registration
    # ------------------------------------------------------------------
    def on_request(self, request_type: str):
        def decorator(func: OverlayRequestHandler):
            self._request_handlers[request_type] = func
            return func
        return decorator

    # ------------------------------------------------------------------
    # High frequency data
    # ------------------------------------------------------------------
    def subscribe_hf(self, obj_type: HighFreqObjType) -> None:
        """Subscribe to high frequency data."""
        self._hf_subscriptions.add(obj_type.__hf_type__)

    def set_window_manager(self, window_manager: "WindowManager") -> None:
        """Attach the WindowManager whose HF mailbox this overlay pulls from.

        Called exactly once, by WindowManager.register_overlay().
        """
        self._window_manager = window_manager

    def get_latest_hf_data(self, type_: Type[HighFreqObjType]) -> Optional[HighFreqObjType]:
        """Pull the latest high frequency data of a specific type from the shared mailbox
        (written directly by the IPC thread; no per-sample cross-thread delivery)."""
        assert self._window_manager is not None, f"{self.OVERLAY_ID} | not registered with a WindowManager"
        return self._window_manager.get_latest_hf_data(type_.__hf_type__)

    def _track_cmd_pipeline_latency(self, event_type: str, sent_ts_ns: int, recv_ts_ns: int) -> None:
        self._stats.track_packet_latency("__CMD_PIPELINE_LATENCY__", "__TOTAL__", sent_ts_ns, recv_ts_ns)
        self._stats.track_packet_latency("__CMD_PIPELINE_LATENCY__", event_type, sent_ts_ns, recv_ts_ns)

    # ------------------------------------------------------------------
    # Default handlers
    # ------------------------------------------------------------------
    def _register_default_handlers(self):
        """Register built-in command and request handlers."""
        @self.on_request("get_window_info")
        def _get_info(_data: dict):
            self.logger.debug('%s | Received request "get_window_info"', self.OVERLAY_ID)
            return self.get_window_info().toJSON()

        @self.on_request("get_window_stats")
        def _get_stats(_data: dict):
            self.logger.debug('%s | Received request "get_window_stats"', self.OVERLAY_ID)
            return self.get_stats()

        @self.on_event("__set_locked_state__")
        def _set_locked(data: dict):
            locked = data.get('new-value', False)
            self.logger.debug('%s | Setting locked state to %s', self.OVERLAY_ID, locked)
            self.set_locked_state(locked)
            if not locked:
                self.set_visibility(True)

        @self.on_event("__toggle_visibility__")
        def _handle_toggle_visibility(_data: Dict[str, Any]):
            self.toggle_visibility()

        @self.on_event("__set_visibility__")
        def _handle_set_visibility(data: Dict[str, Any]):
            visible = data["visible"]
            self.set_visibility(visible)

        @self.on_event("__set_opacity__")
        def _handle_set_opacity(data: Dict[str, Any]):
            opacity = data["opacity"]
            self.opacity = opacity
            self.set_opacity(opacity)

        @self.on_event("__set_config__")
        def _handle_set_window_config(data: Dict[str, Any]) -> None:
            config = OverlayPosition.fromJSON(data)
            self.logger.debug("%s | Setting window config to %s", self.OVERLAY_ID, config)
            self.set_window_position(config)
            self.set_ui_scale(config.scale_factor)

        @self.on_event("__set_telemetry_active__")
        def _handle_set_telemetry_active(data: Dict[str, Any]) -> None:
            active = data["active"]
            self.set_telemetry_active(active)

    # ------------------------------------------------------------------
    # IPC - Signals/Slots
    # ------------------------------------------------------------------
    @Slot(str, bool, str, object)
    def _handle_cmd(self, recipient: str, high_prio: bool, cmd: str, data: Optional[dict]):
        if recipient and recipient != self.OVERLAY_ID:
            return
        if not self.get_visibility() and not high_prio:
            return
        if cmd not in self._handlers:
            return

        if data is None:
            # State topic: the signal is a doorbell only, pull-and-coalesce from the mailbox.
            assert self._window_manager is not None
            data = self._window_manager.take_state_topic(self.OVERLAY_ID, cmd)
            if data is None:
                return

        payload = data["__payload__"]
        timestamp = data["__meta__"]["__timestamp__"]
        self._track_cmd_pipeline_latency(cmd, timestamp, perf_counter_ns())
        try:
            self.dispatch_event(cmd, payload)
        except AssertionError:
            self.logger.exception("%s | Assertion error handling command '%s'", self.OVERLAY_ID, cmd)
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.exception("%s | Error handling command '%s': %s", self.OVERLAY_ID, cmd, e)

    @Slot(str, str, object)
    def _handle_request(self, recipient: str, request_type: str, request_data: object):
        """Internal request dispatcher for overlays."""
        if recipient and recipient != self.OVERLAY_ID:
            return

        if handler := self._request_handlers.get(request_type):
            self.logger.debug("%s | Handling request '%s'", self.OVERLAY_ID, request_type)
            try:
                response = handler(request_data)
                self.response_signal.emit(request_type, response)
            except AssertionError:
                self.logger.exception("%s | Assertion error handling request '%s'", self.OVERLAY_ID, request_type)
                raise
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.exception("%s | Error handling request '%s': %s", self.OVERLAY_ID, request_type, e)
        else:
            self.logger.debug("%s | No handler for request '%s'", self.OVERLAY_ID, request_type)

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
