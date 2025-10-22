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
from typing import Dict

import webview
import win32con
import win32gui

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# Global config - set to 1 or 2
INITIAL_MODE = 2  # 1 = normal, 2 = click-through frameless

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class API:
    def __init__(self, window_id):
        self.window_id = window_id
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
        print(f"[{self.window_id} JS]: {message}")

class WindowManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.windows: Dict[str, webview.Window] = {}
        self.apis: Dict[str, API] = {}
        self.window_modes: Dict[str, int] = {}
        self._running = True

    def _get_shared_utils_path(self) -> str:
        """Construct the absolute path to the shared utils.js file"""
        # From apps/hud/ui/infra -> apps/frontend/js/utils.js
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.logger.debug(f"[WindowManager] Base directory: {base_dir}")

        utils_path = os.path.join(
            base_dir,      # apps/hud/ui/infra
            "..",          # apps/hud/ui
            "..",          # apps/hud
            "..",          # apps
            "frontend",    # apps/frontend
            "js",          # apps/frontend/js
            "utils.js"     # apps/frontend/js/utils.js
        )

        # Normalize the path to remove '..' segments
        utils_path = os.path.normpath(utils_path)
        self.logger.debug(f"[WindowManager] Constructed utils.js path: {utils_path}")

        return utils_path

    def _inject_shared_utils(self, window: webview.Window, window_id: str):
        """Inject shared utility JavaScript into the window"""
        self.logger.info(f"[WindowManager] Attempting to inject shared utils.js into '{window_id}'")

        utils_path = self._get_shared_utils_path()

        # Check if file exists
        if not os.path.exists(utils_path):
            self.logger.error(f"[WindowManager] utils.js NOT FOUND at path: {utils_path}")
            self.logger.error(f"[WindowManager] Current working directory: {os.getcwd()}")
            return False

        self.logger.info(f"[WindowManager] Found utils.js at: {utils_path}")

        try:
            # Read the utils.js file
            self.logger.debug(f"[WindowManager] Reading utils.js file...")
            with open(utils_path, 'r', encoding='utf-8') as f:
                utils_code = f.read()

            file_size = len(utils_code)
            self.logger.info(f"[WindowManager] Read {file_size} bytes from utils.js")

            if file_size == 0:
                self.logger.warning(f"[WindowManager] utils.js is empty!")
                return False

            # Add logging around the utils code (no IIFE wrapper to keep functions global)
            wrapped_code = f"""
                console.log('[UTILS] Injecting shared utils.js...');
                {utils_code}
                console.log('[UTILS] Successfully injected shared utils.js');
            """

            # Inject into window
            self.logger.debug(f"[WindowManager] Evaluating JavaScript in window '{window_id}'...")
            window.evaluate_js(wrapped_code)

            self.logger.info(f"[WindowManager] ✓ Successfully injected utils.js into '{window_id}'")
            return True

        except FileNotFoundError as e:
            self.logger.error(f"[WindowManager] File not found error: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"[WindowManager] Permission error reading utils.js: {e}")
            return False
        except UnicodeDecodeError as e:
            self.logger.error(f"[WindowManager] Encoding error reading utils.js: {e}")
            return False
        except Exception as e:
            self.logger.error(f"[WindowManager] Failed to inject utils.js into '{window_id}': {type(e).__name__}: {e}")
            import traceback
            self.logger.error(f"[WindowManager] Traceback: {traceback.format_exc()}")
            return False

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
            self.logger.info(f"[WindowManager] ✓ Console logger injected into '{window_id}'")
            return True
        except Exception as e:
            self.logger.warning(f"[WindowManager] Could not inject logger for '{window_id}': {e}")
            return False

    def create_window(self, window_id, html_path, x=100, y=100, initial_mode=2):
        """
        Create a new overlay window.
        initial_mode:
            1 = normal (clickable + resizable)
            2 = click-through frameless
        """
        api = API(window_id)
        self.apis[window_id] = api
        self.window_modes[window_id] = initial_mode

        frameless = (initial_mode == 2)
        resizable = (initial_mode == 1)

        window = webview.create_window(
            window_id,
            html_path,
            js_api=api,
            width=350,
            height=420,
            x=x,
            y=y,
            frameless=frameless,
            on_top=True,
            resizable=resizable,
            transparent=True,
        )

        self.windows[window_id] = window

        # Inject utilities and logger after window is ready
        def on_window_ready():

            # Step 1: Inject console logger first so we can see subsequent logs
            self._inject_console_logger(window, window_id)

            # Step 2: Inject shared utils.js
            utils_success = self._inject_shared_utils(window, window_id)

            # if utils_success:
            #     self.logger.info(f"[WindowManager] ✓ All injections successful for '{window_id}'")
            # else:
            #     self.logger.warning(f"[WindowManager] ⚠ Some injections failed for '{window_id}'")

            # Step 3: Apply window mode after everything is loaded
            time.sleep(0.5)  # Give OS time to register the window
            self.set_window_mode(window_id, initial_mode)

        window.events.loaded += on_window_ready

        return window

    def find_window_handle(self, window_id):
        """Find window handle by enumerating all windows"""
        hwnd = None

        def callback(h, _):
            nonlocal hwnd
            if win32gui.IsWindowVisible(h):
                title = win32gui.GetWindowText(h)
                self.logger.debug(f"[WindowManager]   Checking window: '{title}' (hwnd={h})")
                if window_id == title:
                    hwnd = h
                    self.logger.info(f"[WindowManager] ✓ Found window handle for '{window_id}': {hwnd}")
                    return False  # Stop enumeration
            return True

        win32gui.EnumWindows(callback, None)

        if not hwnd:
            # Try alternative approach
            hwnd = win32gui.FindWindow(None, window_id)

        return hwnd

    def set_window_mode(self, window_id, mode):
        """Set mode for a specific window dynamically"""
        self.logger.info(f"[WindowManager] Setting window '{window_id}' to mode {mode}")
        max_attempts = 10
        hwnd = None

        # Try to find the window with retries
        for _ in range(1, max_attempts + 1):
            hwnd = self.find_window_handle(window_id)
            if hwnd:
                break
            time.sleep(0.2)

        if not hwnd:
            self.logger.error(f"[WindowManager] ✗ Window '{window_id}' not found after {max_attempts} attempts")
            return False

        # Update internal state
        self.window_modes[window_id] = mode

        if mode == 1:
            # Normal mode
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style &= ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style |= win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_THICKFRAME
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        else:
            # Click-through frameless
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

        # Apply changes
        win32gui.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            win32con.SWP_FRAMECHANGED | win32con.SWP_NOMOVE |
            win32con.SWP_NOSIZE | win32con.SWP_NOZORDER
        )

        self.logger.info(f"[WindowManager] ✓ Window '{window_id}' mode successfully changed to {mode}")
        return True

    def toggle_mode(self, window_id):
        """Convenience method to switch between normal and click-through"""
        current = self.window_modes.get(window_id, 1)
        new_mode = 2 if current == 1 else 1
        self.logger.debug(f"[WindowManager] Current mode: {current}, New mode: {new_mode}")
        self.set_window_mode(window_id, new_mode)
        return new_mode

    def toggle_mode_all(self):
        """Toggle mode for all managed windows"""
        for window_id in self.windows.keys():
            self.toggle_mode(window_id)

    def broadcast_data(self, data):
        for window_id, api in self.apis.items():
            api.data.update(data)
            if window := self.windows.get(window_id):
                self._push_to_window(window, window_id, data)

    def unicast_data(self, window_id, data):
        if api := self.apis.get(window_id):
            api.data.update(data)
        if window := self.windows.get(window_id):
            self._push_to_window(window, window_id, data)

    def _push_to_window(self, window: webview.Window, window_id, data):
        """Push data update to JavaScript via custom event"""
        try:
            # Convert data to JSON string for JS
            data_json = json.dumps(data)

            # Dispatch custom event to JS
            js_code = f"""
                (function() {{
                    const event = new CustomEvent('telemetry-update', {{
                        detail: {data_json}
                    }});
                    window.dispatchEvent(event);
                }})();
            """
            window.evaluate_js(js_code)
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error(f"[WindowManager] ✗ Failed to push data to '{window_id}': {type(e).__name__}: {e}")

    def stop(self):
        """Stop telemetry updates and close windows"""
        self.logger.info("[WindowManager] Stopping WindowManager...")
        self._running = False
        for window_id, window in self.windows.items():
            try:
                window.destroy()
                self.logger.info(f"[WindowManager] ✓ Closed window '{window_id}'")
            except Exception as e: # pylint: disable=broad-except
                self.logger.error(f"[WindowManager] Failed to close window '{window_id}': {e}")
        self.logger.info("[WindowManager] All windows closed")

    def race_table_update(self, data):
        """Handle race table update"""
        # self.logger.debug(f"[WindowManager] Race table update received")
        self.unicast_data("lap_timer", data)
