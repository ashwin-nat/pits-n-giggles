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
from typing import Any, Callable, Dict, Set

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIcon

from apps.hud.common import deserialise_data, serialise_data
from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.infra.high_freq_types import HighFreqBase
from lib.assets_loader import load_icon
from meta.meta import APP_NAME_SNAKE

# -------------------------------------- TYPES -------------------------------------------------------------------------

OverlayCommandHandler = Callable[[Dict[str, Any]], None] # Takes dict arg, returns None
OverlayRequestHandler = Callable[[Dict[str, Any]], str] # Takes dict arg, returns str (serialised JSON)
OverlayHighFreqHandler = Callable[[HighFreqBase], None] # Takes high-freq payload, returns None

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BaseOverlay():
    """
    Framework-agnostic overlay base class providing the core overlay lifecycle,
    configuration handling, and inter-process command/request infrastructure.

    This class contains *no* UI toolkit assumptions. It does not depend on
    QWidget or QML. Instead, it defines the high-level behavior shared by all
    overlay types (Widget or QML), while delegating rendering and windowing to
    derived classes.

    Responsibilities provided by BaseOverlay:
    -----------------------------------------
    - Stores overlay identity, configuration, and runtime state.
    - Defines the IPC mechanism for overlay commands and requests.
      Derived overlays automatically gain:
        - `on_event()` decorator for command handlers
        - `on_request()` decorator for request/response handlers
        - Automatic dispatch via `_handle_cmd()` and `_handle_request()`
    - Manages default commands such as:
        - toggling visibility (fade in/out)
        - updating locked state
        - setting opacity
        - applying new configuration
        - returning geometry/position (`get_window_info`)
    - Drives UI lifecycle by calling:
        - `_setup_window()`     (implemented by UI subclass)
        - `build_ui()`          (implemented by UI subclass)
        - `apply_config()`      (UI-specific geometry/opacity)
    - Ensures UI rebuilds occur when scale factor changes.

    What derived classes must implement:
    ------------------------------------
    Derived classes (e.g., BaseOverlayWidget or BaseOverlayQML) must implement:
        - `set_window_title()`   - set window title
        - `set_window_icon()`    - set window icon
        - `build_ui()`           - construct the UI
        - `apply_config()`       - apply geometry and opacity
        - `update_window_flags()`- locked mode / windowed overlay behavior
        - `set_opacity()`        - apply opacity to the backend window
        - `set_locked_state()`   - enable/disable interaction
        - `animate_fade()`       - fade in/out using toolkit-specific animation
        - `get_window_info()`    - return window geometry
        - `set_window_position()`- set window position and update self.config
        - `toggle_visibility()`  - fade in/out
        - `set_ui_scale()`       - set scale factor

    When to subclass BaseOverlay:
    ------------------------------
    Do not subclass BaseOverlay directly for new overlays. Instead subclass one of:
        - BaseOverlayWidget  - for QWidget-based overlays
        - BaseOverlayQML     - for QML-based overlays

    BaseOverlay deliberately contains no UI behavior so that multiple rendering
    technologies can coexist and share the same command/IPC infrastructure.

    Subclass BaseOverlay only if you need to add new UI-specific behavior.
    """
    response_signal = Signal(str, str)   # request_type, response_data (serialised JSON)

    def __init__(self,
                 overlay_id: str,
                 config: OverlaysConfig,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool):

        self.overlay_id = overlay_id
        self.windowed_overlay = windowed_overlay
        self.config = config
        self.locked = locked
        self.logger = logger
        self.opacity = opacity
        self.scale_factor = scale_factor
        self._command_handlers: Dict[str, OverlayCommandHandler] = {}
        self._request_handlers: Dict[str, OverlayRequestHandler] = {}
        self._high_freq_handlers: Dict[str, Callable[[Any], None]] = {}

        # Create the actual window backend (widget or QML)
        self._setup_window()
        self.build_ui()
        self.apply_config()

        # Register default handlers
        self._register_default_handlers()

    # ----------------------------------------------------------------------
    # Abstract interface — implemented by QWidget and QML subclasses
    # ----------------------------------------------------------------------
    def _setup_window(self):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME_SNAKE)
        self.set_window_title(self.overlay_id)
        self.set_window_icon(load_icon(Path("assets") / "logo.png",
                                     debug_log_printer=self.logger.debug,
                                     error_log_printer=self.logger.error))

    def set_window_title(self, title: str):
        raise NotImplementedError

    def set_window_icon(self, icon: QIcon):
        raise NotImplementedError

    def build_ui(self):
        raise NotImplementedError

    def apply_config(self):
        raise NotImplementedError

    def update_window_flags(self):
        raise NotImplementedError

    def set_opacity(self, opacity: int):
        raise NotImplementedError

    def set_locked_state(self, locked: bool):
        raise NotImplementedError

    def animate_fade(self, show: bool):
        raise NotImplementedError

    def get_window_info(self) -> OverlaysConfig:
        raise NotImplementedError

    def set_window_position(self, config: OverlaysConfig):
        raise NotImplementedError

    def toggle_visibility(self):
        raise NotImplementedError

    def set_ui_scale(self, ui_scale: float):
        raise NotImplementedError

    # ----------------------------------------------------------------------
    # Command/Request handler registration
    # ----------------------------------------------------------------------
    def on_event(self, cmd_name: str):
        def decorator(func: OverlayCommandHandler):
            self._command_handlers[cmd_name] = func
            return func
        return decorator

    def on_request(self, request_type: str):
        def decorator(func: OverlayRequestHandler):
            self._request_handlers[request_type] = func
            return func
        return decorator

    def on_high_freq(self, hf_type: str):
        def decorator(func: OverlayHighFreqHandler):
            self._high_freq_handlers[hf_type] = func
            return func
        return decorator

    # ----------------------------------------------------------------------
    # Default handlers (same as before)
    # ----------------------------------------------------------------------
    def _register_default_handlers(self):
        """Register built-in request handlers."""
        @self.on_request("get_window_info")
        def _get_info(_data: dict):
            """Return current position as an OverlaysConfig."""
            self.logger.debug(f'{self.overlay_id} | Received request "get_window_info"')
            return serialise_data(self.get_window_info().toJSON())

        @self.on_event("set_locked_state")
        def _set_locked(data: dict):
            """Set locked state."""
            locked = data.get('new-value', False)
            self.logger.debug(f'{self.overlay_id} | Setting locked state to {locked}')
            self.set_locked_state(locked)

        @self.on_event("toggle_visibility")
        def _handle_toggle_visibility(_data: Dict[str, Any]):
            """Toggle visibility."""
            self.toggle_visibility()

        @self.on_event("set_opacity")
        def _handle_set_opacity(data: Dict[str, Any]):
            """Set opacity."""
            opacity = data["opacity"]
            self.set_opacity(opacity)
            self.opacity = opacity

        @self.on_event("set_config")
        def _handle_set_window_config(data: Dict[str, Any]) -> None:
            """Set window config."""
            config = OverlaysConfig.fromJSON(data)
            self.logger.debug(f"{self.overlay_id} | Setting window config to {config}")
            self.set_window_position(config)

        @self.on_event("set_scale_factor")
        def _handle_set_scale_factor(data: Dict[str, Any]) -> None:
            """Set UI scale factor"""
            scale_factor = data["scale_factor"]
            self.logger.debug(f"{self.overlay_id} | Setting UI scale to {scale_factor}")
            self.set_ui_scale(scale_factor)
            self.scale_factor = scale_factor

    # ----------------------------------------------------------------------
    # IPC — Signals/Slots
    # ----------------------------------------------------------------------
    @Slot(set, str, str)
    def _handle_cmd(self, recipients: Set[str], cmd: str, data: str):
        if recipients and self.overlay_id not in recipients:
            return
        handler = self._command_handlers.get(cmd)
        if not handler:
            return
        parsed = deserialise_data(data)
        try:
            handler(parsed)
        except AssertionError:
            self.logger.exception(f"{self.overlay_id} | Assertion error handling command '{cmd}'")
            raise # We want to crash on assertions for debugging
        except Exception as e: # pylint: disable=broad-except
            self.logger.exception(f"{self.overlay_id} | Error handling command '{cmd}': {e}")

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

    @Slot(set, object)
    def _handle_high_freq_data(self, recipients: Set[str], payload: HighFreqBase):
        if self.overlay_id not in recipients:
            return

        if handler := self._high_freq_handlers.get(payload.__hf_type__):
            try:
                handler(payload)
            except AssertionError:
                self.logger.exception(f"{self.overlay_id} | Assertion error handling command '{payload.__hf_type__}'")
                raise # We want to crash on assertions for debugging
            except Exception as e: # pylint: disable=broad-except
                self.logger.exception(f"{self.overlay_id} | Error handling command '{payload.__hf_type__}': {e}")
