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
import json
import logging
import os
import time
import traceback
from threading import Lock, Thread
from typing import Dict, Optional

import webview
import win32con
import win32gui

from .config import OverlaysConfig

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class API:
    def __init__(self, window_id, logger=None):
        self.window_id = window_id
        self.logger: Optional[logging.Logger] = logger
        self.data = {
            'speed': 0,
            'rpm': 0,
            'gear': 1,
            'lap_time': '0:00.000'
        }

    def get_data(self):
        """Called from JS to get current telemetry data"""
        return self.data

    # Capture console logs from JS
    def log(self, message):
        if self.logger:
            self.logger.debug(f"[{self.window_id} JS]: {message}")

class WindowManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.windows: Dict[str, webview.Window] = {}
        self.apis: Dict[str, API] = {}
        self._running = True
        self._windows_visible = True
        self._window_lock = Lock()
        self._hwnd_cache = {}

        # Configure scripts to inject
        self.injectable_scripts = [
            {
                'name': 'utils.js',
                'path_segments': ['..', '..', '..', 'frontend', 'js', 'utils.js'],
                'description': 'Shared utility functions'
            },
        ]

    def _construct_script_path(self, path_segments: list) -> str:
        """Construct an absolute path from base directory and path segments"""
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Join all segments
        script_path = os.path.join(base_dir, *path_segments)

        # Normalize the path to remove '..' segments
        return os.path.normpath(script_path)

    def _inject_script(self, window: webview.Window, window_id: str, script_name: str, script_path: str) -> bool:
        """Inject a JavaScript file into the window"""
        self.logger.debug(f"[WindowManager] Attempting to inject {script_name} into '{window_id}'")

        # Check if file exists
        if not os.path.exists(script_path):
            self.logger.error(f"[WindowManager] {script_name} NOT FOUND at path: {script_path}")
            return False

        self.logger.debug(f"[WindowManager] Found {script_name} at: {script_path}")

        try:
            # Read the script file
            self.logger.debug(f"[WindowManager] Reading {script_name} file...")
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()

            file_size = len(script_code)
            self.logger.debug(f"[WindowManager] Read {file_size} bytes from {script_name}")

            if file_size == 0:
                self.logger.warning(f"[WindowManager] {script_name} is empty!")
                return False

            # Wrap with logging
            wrapped_code = f"""
                console.log('[INJECT] Loading {script_name}...');
                {script_code}
                console.log('[INJECT] Successfully loaded {script_name}');
            """

            # Inject into window
            self.logger.debug(f"[WindowManager] Evaluating {script_name} in window '{window_id}'...")
            window.evaluate_js(wrapped_code)

            self.logger.debug(f"[WindowManager] Successfully injected {script_name} into '{window_id}'")
            return True

        except FileNotFoundError as e:
            self.logger.error(f"[WindowManager] File not found error for {script_name}: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"[WindowManager] Permission error reading {script_name}: {e}")
            return False
        except UnicodeDecodeError as e:
            self.logger.error(f"[WindowManager] Encoding error reading {script_name}: {e}")
            return False
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] Failed to inject {script_name} into '{window_id}': {type(e).__name__}: {e}")
            self.logger.error(f"[WindowManager] Traceback: {traceback.format_exc()}")
            return False

    def _inject_all_scripts(self, window: webview.Window, window_id: str) -> dict:
        """Inject all configured scripts into the window"""
        results = {}

        for script_config in self.injectable_scripts:
            script_name = script_config['name']
            script_path = self._construct_script_path(script_config['path_segments'])

            self.logger.debug(f"[WindowManager] Injecting {script_name} ({script_config.get('description', 'No description')})")
            success = self._inject_script(window, window_id, script_name, script_path)
            results[script_name] = success

        # Log summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)

        if successful == total:
            self.logger.debug(f"[WindowManager] All {total} scripts injected successfully for '{window_id}'")
        else:
            self.logger.warning(f"[WindowManager] {successful}/{total} scripts injected for '{window_id}'")

        # Dispatch utils-ready event after all scripts are loaded
        self._dispatch_utils_ready(window, window_id)

        return results

    def _inject_console_logger(self, window: webview.Window, window_id: str):
        """Inject console logging interceptor into the window"""
        self.logger.debug(f"[WindowManager] Injecting console logger into '{window_id}'")

        js_code = """
            (function() {
                console.log('[LOGGER] Setting up console interceptors...');

                const origLog = console.log;
                console.log = function(...args) {
                    window.pywebview.api.log(args.join(' '));
                    origLog.apply(console, args);
                };

                const origErr = console.error;
                console.error = function(...args) {
                    window.pywebview.api.log('[ERROR] ' + args.join(' '));
                    origErr.apply(console, args);
                };

                const origWarn = console.warn;
                console.warn = function(...args) {
                    window.pywebview.api.log('[WARN] ' + args.join(' '));
                    origWarn.apply(console, args);
                };

                console.log('[LOGGER] Console interceptors ready');
            })();
        """

        try:
            window.evaluate_js(js_code)
            self.logger.debug(f"[WindowManager] Console logger injected into '{window_id}'")
            return True
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.warning(f"[WindowManager] Could not inject logger for '{window_id}': {e}")
            return False

    def _dispatch_utils_ready(self, window: webview.Window, window_id: str):
        """Dispatch utils-ready event to notify JavaScript that all scripts are loaded"""
        self.logger.debug(f"[WindowManager] Dispatching utils-ready event for '{window_id}'")

        js_code = """
            (function() {
                console.log('[WindowManager] Dispatching utils-ready event...');
                const event = new Event('utils-ready');
                window.dispatchEvent(event);
                console.log('[WindowManager] utils-ready event dispatched');
            })();
        """

        try:
            window.evaluate_js(js_code)
            self.logger.debug(f"[WindowManager] utils-ready event dispatched for '{window_id}'")
            return True
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] Failed to dispatch utils-ready for '{window_id}': {e}")
            return False

    def create_window(self, window_id: str, html_path: str, params: OverlaysConfig) -> None:
        """
        Create a new overlay window. Windows are created in a locked state by default.

        Args:
            window_id: Unique identifier for the window
            html_path: Path to the HTML file to load in the window
            params: Window parameters
        """
        api = API(window_id, self.logger)
        self.apis[window_id] = api

        self.logger.debug(f"[WindowManager] Creating window '{window_id}' at ({params.x}, {params.y}) for {html_path}")
        assert os.path.exists(html_path)

        window = webview.create_window(
            window_id,
            html_path,
            js_api=api,
            width=params.width,
            height=params.height,
            x=params.x,
            y=params.y,
            frameless=True,
            on_top=True,
            resizable=False,
            transparent=True,
        )

        self.windows[window_id] = window

        # Store params for use in callback
        window._init_params = params
        window._window_id = window_id

        # Inject utilities and logger after window is ready
        window.events.loaded += self._on_window_loaded
        return window

    def _on_window_loaded(self, window):
        """Callback when window is loaded - inject scripts and configure window"""
        window_id = window._window_id
        params = window._init_params

        self.logger.debug(f"[WindowManager] Window '{window_id}' loaded callback started")

        try:
            # Step 1: Inject console logger
            self._inject_console_logger(window, window_id)

            # Step 2: Inject all scripts
            self._inject_all_scripts(window, window_id)

            # Step 3: Schedule window configuration in a separate thread to avoid blocking
            # NEW: Use thread to prevent blocking other window loads
            config_thread = Thread(
                target=self._configure_window_delayed,
                args=(window_id, params),
                daemon=True,
                name=f"ConfigThread-{window_id}"
            )
            config_thread.start()

            self.logger.debug(f"[WindowManager] Window '{window_id}' loaded callback completed")

        except Exception as e:
            self.logger.error(f"[WindowManager] Error in _on_window_loaded for '{window_id}': {e}")
            self.logger.error(traceback.format_exc())

    def _configure_window_delayed(self, window_id: str, params: OverlaysConfig):
        """Configure window after a delay - runs in separate thread"""
        try:
            self.logger.debug(f"[WindowManager] Starting delayed config for '{window_id}'")

            # Give the window time to fully initialize
            time.sleep(0.3)

            # Use lock to prevent race conditions
            with self._window_lock:
                self.logger.debug(f"[WindowManager] Acquired lock for '{window_id}' configuration")

                # Apply locked state
                if self.set_window_locked_state(window_id, True):
                    self.logger.debug(f"[WindowManager] Successfully locked '{window_id}'")
                else:
                    self.logger.warning(f"[WindowManager] Failed to lock '{window_id}'")

                # Small delay between operations
                time.sleep(0.1)

                # Apply dimensions
                if self._apply_window_dimensions(window_id, params):
                    self.logger.debug(f"[WindowManager] Successfully applied dimensions to '{window_id}'")
                else:
                    self.logger.warning(f"[WindowManager] Failed to apply dimensions to '{window_id}'")

            self.logger.debug(f"[WindowManager] Completed delayed config for '{window_id}'")

        except Exception as e:
            self.logger.error(f"[WindowManager] Error in delayed config for '{window_id}': {e}")
            self.logger.error(traceback.format_exc())

    def _apply_window_dimensions(self, window_id: str, params: OverlaysConfig) -> bool:
        """Force window to specific dimensions after creation

        Args:
            window_id: Unique identifier for the window
            params: Window parameters with x, y, width, height

        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.debug(f"[WindowManager] Applying dimensions to '{window_id}': {params.width}x{params.height} at ({params.x}, {params.y})")

        hwnd = self.find_window_handle(window_id)
        if not hwnd:
            self.logger.error(f"[WindowManager] Window '{window_id}' not found for dimension adjustment")
            return False

        try:
            # Use SetWindowPos to force exact dimensions
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST, # Keep on top
                params.x,
                params.y,
                params.width,
                params.height,
                win32con.SWP_SHOWWINDOW
            )

            self.logger.debug(f"[WindowManager] Applied dimensions to '{window_id}': {params.width}x{params.height} at ({params.x}, {params.y})")
            return True

        except Exception as e:
            self.logger.error(f"[WindowManager] Failed to apply dimensions to '{window_id}': {type(e).__name__}: {e}")
            return False

    def find_window_handle(self, window_id: str, max_retries: int = 3) -> Optional[int]:
        """Find window handle with retry logic - NEW: Added caching and retry"""
        # Check cache first
        if window_id in self._hwnd_cache:
            hwnd = self._hwnd_cache[window_id]
            # Verify cached handle is still valid
            try:
                if win32gui.IsWindow(hwnd):
                    return hwnd
                else:
                    # Cached handle is invalid, remove from cache
                    del self._hwnd_cache[window_id]
            except Exception:
                del self._hwnd_cache[window_id]

        # Try to find the window with retries
        for attempt in range(max_retries):
            self.logger.debug(f"[WindowManager] Finding window '{window_id}' (attempt {attempt + 1}/{max_retries})")

            hwnd = None

            def callback(h, _):
                nonlocal hwnd
                try:
                    if win32gui.IsWindowVisible(h):
                        title = win32gui.GetWindowText(h)
                        if window_id == title:
                            hwnd = h
                            self.logger.debug(f"[WindowManager] Found '{window_id}' at hwnd={hwnd}")
                            return False  # Stop enumeration
                except Exception as e:
                    # Skip windows that cause errors during enumeration
                    self.logger.debug(f"[WindowManager] Error checking window {h}: {e}")
                return True

            try:
                win32gui.EnumWindows(callback, None)
            except Exception as e:
                self.logger.error(f"[WindowManager] Error during window enumeration: {e}")

            if hwnd:
                # Cache the found handle
                self._hwnd_cache[window_id] = hwnd
                return hwnd

            # If not found, try alternative approach
            try:
                hwnd = win32gui.FindWindow(None, window_id)
                if hwnd:
                    self._hwnd_cache[window_id] = hwnd
                    return hwnd
            except Exception as e:
                self.logger.debug(f"[WindowManager] FindWindow failed: {e}")

            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(0.2)

        self.logger.error(f"[WindowManager] Could not find window '{window_id}' after {max_retries} attempts")
        return None

    def set_window_locked_state(self, window_id: str, locked: bool) -> bool:
        """Set locked state for a specific window"""
        self.logger.debug(f"[WindowManager] Setting window '{window_id}' locked state to {locked}")

        hwnd = self.find_window_handle(window_id)
        if not hwnd:
            self.logger.error(f"[WindowManager] Window '{window_id}' not found")
            return False

        try:
            if locked:
                # Locked mode (frameless, click-through)
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex_style |= (
                    win32con.WS_EX_LAYERED
                    | win32con.WS_EX_TRANSPARENT
                    | win32con.WS_EX_NOACTIVATE
                    | win32con.WS_EX_TOOLWINDOW
                )
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
                ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(ctypes.c_int(-1)))
                ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x2)

                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style &= ~(win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_THICKFRAME)
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            else:
                # Unlocked mode (frameless but resizable)
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex_style &= ~(win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style &= ~(win32con.WS_CAPTION | win32con.WS_SYSMENU)
                style |= win32con.WS_THICKFRAME
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

            # Apply changes
            win32gui.SetWindowPos(
                hwnd, None, 0, 0, 0, 0,
                win32con.SWP_FRAMECHANGED | win32con.SWP_NOMOVE |
                win32con.SWP_NOSIZE | win32con.SWP_NOZORDER
            )

            self.logger.debug(f"[WindowManager] Window '{window_id}' locked state successfully changed to {locked}")
            return True

        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] Failed to set locked state for '{window_id}': {e}")
            return False

    def set_locked_state(self, window_id: str, locked_state_dict: Dict[str, bool]):
        """Set locked state for a specific window based on the new-value in the dict"""
        new_locked_state = locked_state_dict.get('new-value')
        if new_locked_state is None:
            self.logger.error(f"[WindowManager] 'new-value' not found in locked_state_dict for window '{window_id}'")
            return False
        self.logger.debug(f"[WindowManager] Setting locked state for '{window_id}' to {new_locked_state}")
        return self.set_window_locked_state(window_id, new_locked_state)

    def set_locked_state_all(self, locked_state_dict: Dict[str, bool]) -> bool:
        """Set locked state for all managed windows based on the new-value in the dict"""
        new_locked_state = locked_state_dict.get('new-value')
        if new_locked_state is None:
            self.logger.error("[WindowManager] 'new-value' not found in locked_state_dict for all windows")
            return False
        self.logger.debug(f"[WindowManager] Setting locked state for all windows to {new_locked_state}")
        with self._window_lock:
            for window_id in self.windows:
                self.set_window_locked_state(window_id, new_locked_state)
        self.broadcast_lock_state_change(locked_state_dict)
        return True

    def broadcast_data(self, data):
        for window_id, api in self.apis.items():
            api.data.update(data)
            if window := self.windows.get(window_id):
                self._push_to_window(window, window_id, 'telemetry-update', data)

    def unicast_data(self, window_id: str, data: dict):
        if api := self.apis.get(window_id):
            api.data.update(data)
        if window := self.windows.get(window_id):
            self._push_to_window(window, window_id, 'telemetry-update', data)

    def broadcast_lock_state_change(self, data):
        for window_id, api in self.apis.items():
            api.data.update(data)
            if window := self.windows.get(window_id):
                self._push_to_window(window, window_id, 'lock-state-change', data)

    def _push_to_window(self, window: webview.Window, window_id: str, event_name: str, data: dict):
        """Push data update to JavaScript via custom event"""
        try:
            # Convert data to JSON string for JS
            data_json = json.dumps(data)

            # Dispatch custom event to JS
            js_code = f"""
                (function() {{
                    const event = new CustomEvent('{event_name}', {{
                        detail: {data_json}
                    }});
                    window.dispatchEvent(event);
                }})();
            """
            window.evaluate_js(js_code)
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] Failed to push data to '{window_id}': {e}")

    def get_window_info(self, window_id):
        """Get size and position information for a specific window

        Returns:
            dict: Dictionary containing window information with keys:
                - x (int): X coordinate of window's left edge
                - y (int): Y coordinate of window's top edge
                - width (int): Window width in pixels
                - height (int): Window height in pixels
                - right (int): X coordinate of window's right edge
                - bottom (int): Y coordinate of window's bottom edge
            None: If window not found or error occurs
        """
        self.logger.debug(f"[WindowManager] Getting info for window '{window_id}'")

        hwnd = self.find_window_handle(window_id)
        if not hwnd:
            self.logger.error(f"[WindowManager] Window '{window_id}' not found")
            return None

        try:
            # Get window rectangle (left, top, right, bottom)
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect

            window_info = OverlaysConfig(
                x=left,
                y=top,
                width=(right - left),
                height=(bottom - top),
            )

            self.logger.debug(f"[WindowManager] Window '{window_id}' info: {window_info}")
            return window_info

        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] Failed to get info for window '{window_id}': {type(e).__name__}: {e}")
            return None

    def toggle_visibility_all(self) -> bool:
        """Toggle visibility for all managed windows

        Returns:
            bool: True if all operations successful, False otherwise
        """
        self._windows_visible = not self._windows_visible
        self.logger.debug(f"[WindowManager] Setting visibility for all windows to {self._windows_visible}")

        success_count = 0
        with self._window_lock:
            for window_id in self.windows:
                if self.set_window_visibility(window_id, self._windows_visible):
                    success_count += 1

        self.logger.debug(f"[WindowManager] Set visibility for {success_count}/{len(self.windows)} windows")
        return success_count == len(self.windows)

    def set_window_visibility(self, window_id: str, visible: bool) -> bool:
        """Set visibility state for a specific window

        Args:
            window_id: Unique identifier for the window
            visible: True to show window, False to hide

        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.debug(f"[WindowManager] Setting window '{window_id}' visibility to {visible}")

        hwnd = self.find_window_handle(window_id)
        if not hwnd:
            self.logger.error(f"[WindowManager] Window '{window_id}' not found")
            return False

        try:
            if visible:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

            self.logger.debug(f"[WindowManager] Window '{window_id}' visibility successfully changed to {visible}")
            return True

        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] Failed to set visibility for '{window_id}': {e}")
            return False
    def stop(self):
        """Stop telemetry updates and close all windows safely."""
        self.logger.debug("[WindowManager] Stopping WindowManager...")
        self._running = False

        # Copy keys to avoid modifying dict during iteration
        with self._window_lock:
            for window_id in list(self.windows.keys()):
                window = self.windows[window_id]
                try:
                    # Detach event handlers if any to prevent callbacks after destroy
                    if hasattr(window, 'events'):
                        try:
                            window.events.closed.clear() # remove all closed handlers
                        except Exception: # pylint: disable=broad-except
                            pass

                    # Destroy the window if it still exists
                    if window and getattr(window, "webview_window", None):
                        window.destroy()
                        self.logger.info(f"[WindowManager] Closed window '{window_id}'")
                # Catch any PyWebView / WebView2 teardown errors
                except Exception as e: # pylint: disable=broad-exception-caught
                    self.logger.error(f"[WindowManager] Failed to close window '{window_id}': {e}")

            # Short delay to allow WebView2 cleanup
            time.sleep(0.05)

            # Clear the window registry
            self.windows.clear()
            self._hwnd_cache.clear()

        self.logger.info("[WindowManager] All windows closed")
