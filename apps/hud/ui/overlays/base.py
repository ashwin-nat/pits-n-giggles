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
from typing import Any, Callable, Dict

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QWidget

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.common import serialise_data, deserialise_data

# -------------------------------------- TYPES -------------------------------------------------------------------------

OverlayCommandHandler = Callable[[Dict[str, Any]], None] # Takes dict arg, returns None
OverlayRequestHandler = Callable[[Dict[str, Any]], str] # Takes dict arg, returns str (serialised JSON)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlay(QWidget):
    # Add signal for responses
    response_signal = Signal(str, object)  # request_type, response_data

    def __init__(self,
                 overlay_id: str,
                 config: OverlaysConfig,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float):
        """Initialize base overlay.

        Args:
            overlay_id (str): Overlay ID
            config (OverlaysConfig): Overlay config
            logger (logging.Logger): Logger object
            locked (bool): Locked state
            opacity (int): Window opacity
            scale_factor (float): UI Scale factor (multiplier)
        """
        super().__init__()
        self.overlay_id = overlay_id
        self.setObjectName(self.overlay_id)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.config = config
        self.locked = locked
        self.logger = logger
        self.opacity = opacity
        self.scale_factor = scale_factor
        self._drag_pos = None
        self._command_handlers: Dict[str, OverlayCommandHandler] = {}
        self._request_handlers: Dict[str, OverlayRequestHandler] = {}  # New: request handlers
        self._icon_cache: Dict[str, QIcon] = {}
        self._setup_window()
        self.build_ui()
        self.apply_config()
        self.adjustSize()

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
        # self.setGeometry(
        #     self.config.x,
        #     self.config.y,
        #     self.config.width,
        #     self.config.height
        # )
        # TODO: finalise
        self.move(self.config.x, self.config.y)
        self.set_opacity(self.opacity)

    def set_opacity(self, opacity: int):
        """Set window opacity (0-100)."""
        self.opacity = opacity
        self.logger.debug(f"{self.overlay_id} | Setting opacity to {opacity}%")
        self.setWindowOpacity(self.opacity / 100.0)

    # --------------------------------------------------------------------------
    # Window State
    # --------------------------------------------------------------------------
    def update_window_flags(self):
        """Refresh window flags based on locked state."""
        # Click-through when locked, normal interaction when unlocked
        if self.locked:
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)
            # Remove border when locked
            self.setStyleSheet(f"""
                QWidget#{self.overlay_id} {{
                    border: none;
                }}
            """)
        else:
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
            # Add border when unlocked
            self.setStyleSheet(f"""
                QWidget#{self.overlay_id} {{
                    border: 2px solid rgba(255, 255, 255, 0.9);
                }}
            """)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint
        )
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
    def on_event(self, cmd_name: str):
        """Flask-style decorator for registering command handlers."""
        def decorator(func: OverlayCommandHandler):
            self._command_handlers[cmd_name] = func
            return func
        return decorator

    def _register_default_handlers(self):
        """Register built-in request handlers."""
        @self.on_request("get_window_info")
        def _handle_get_window_info(_data: Dict[str, Any]) -> str:
            """Return current geometry as an OverlaysConfig."""
            self.logger.debug(f'{self.overlay_id} | Received request "get_window_info"')
            return serialise_data(self.get_window_info().toJSON())

        @self.on_event("set_locked_state")
        def _handle_set_locked_state(data: Dict[str, Any]):
            """Set locked state."""
            locked = data.get('new-value', False)
            self.logger.debug(f'{self.overlay_id} | Setting locked state to {locked}')
            self.set_locked_state(locked)

        @self.on_event("toggle_visibility")
        def _handle_toggle_visibility(_data: Dict[str, Any]):
            """Toggle visibility."""
            self.logger.debug(f'{self.overlay_id} | Toggling visibility')
            if self.isVisible():
                self.logger.debug(f'{self.overlay_id} | Hiding overlay')
                self.hide()
            else:
                self.logger.debug(f'{self.overlay_id} | Showing overlay')
                self.show()

        @self.on_event("set_opacity")
        def _handle_set_opacity(data: Dict[str, Any]):
            """Set opacity."""
            opacity = data["opacity"]
            self.set_opacity(opacity)

        @self.on_event("set_config")
        def _handle_set_window_config(data: Dict[str, Any]) -> None:
            """Set window config."""
            config = OverlaysConfig.fromJSON(data)
            self.logger.debug(f"{self.overlay_id} | Setting window config to {config}")
            self.setGeometry(config.x, config.y, config.width, config.height)

        @self.on_event("set_scale_factor")
        def _handle_set_scale_factor(data: Dict[str, Any]) -> None:
            """Set UI scale factor"""
            self.scale_factor = data["scale_factor"]
            self.logger.debug(f"{self.overlay_id} | Setting UI scale to {self.scale_factor}")
            self.rebuild_ui()
            self.adjustSize()

    def on_request(self, request_type: str):
        """Flask-style Decorator for registering request handlers that return responses."""
        def decorator(func: Callable[[dict], Any]):
            self._request_handlers[request_type] = func
            return func
        return decorator

    @Slot(str, str, dict)
    def _handle_request(self, recipient: str, request_type: str, request_data: str):
        """Internal request dispatcher for overlays.

        Args:
            recipient (str): Overlay ID that sent the request
            request_type (str): Request type
            request_data (str): Request data JSON serialized as a string
        """
        if recipient and recipient != self.overlay_id:
            return  # Not for this overlay

        if handler := self._request_handlers.get(request_type):
            self.logger.debug(f"{self.overlay_id} | Handling request '{request_type}'")
            parsed_data = deserialise_data(request_data)
            try:
                response = handler(parsed_data)
                # Emit response back through window manager
                self.response_signal.emit(request_type, response)
            except AssertionError:
                self.logger.exception(f"{self.overlay_id} | Assertion error handling request '{request_type}'")
                raise # We want to crash on assertions for debugging
            except Exception as e: # pylint: disable=broad-except
                self.logger.exception(f"{self.overlay_id} | Error handling request '{request_type}': {e}")
        else:
            self.logger.debug(f"{self.overlay_id} | No handler for request '{request_type}'")

    # Existing _handle_cmd method stays the same
    @Slot(str, str, str)
    def _handle_cmd(self, recipient: str, cmd: str, data: str):
        """Internal command dispatcher for overlays.

        Args:
            recipient (str): Overlay ID that sent the command
            cmd (str): Command
            data (str): Command data JSON serialized as a string
        """
        if recipient and recipient != self.overlay_id:
            return  # Not for this overlay

        if handler := self._command_handlers.get(cmd):
            parsed_data = deserialise_data(data)
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
            self.logger.debug(f"{self.overlay_id} | Cleaning widget: {w.__class__.__name__}")
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
