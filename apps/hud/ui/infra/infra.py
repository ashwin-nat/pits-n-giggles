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
            width=400,
            height=300,
            x=x,
            y=y,
            frameless=frameless,
            on_top=True,
            resizable=resizable
        )

        self.windows[window_id] = window

        # Inject JS logger and apply mode after window is ready
        def on_window_ready():
            # Inject logger
            js_code = """
                (function() {
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
                })();
            """
            try:
                window.evaluate_js(js_code)
            except Exception as e:
                print(f"[WARN] Could not inject logger for {window_id}: {e}")

            # Apply mode after window is fully loaded
            time.sleep(0.5)  # Give OS time to register the window
            self.set_window_mode(window_id, initial_mode)

        window.events.loaded += on_window_ready

        return window

    def find_window_handle(self, window_id):
        """Find window handle by enumerating all windows"""
        hwnd = None

        def callback(h, extra):
            nonlocal hwnd
            if win32gui.IsWindowVisible(h):
                title = win32gui.GetWindowText(h)
                print(f"In callback: found window title: {title}")
                if window_id == title:
                    hwnd = h
                    print(f"[INFO] Found window handle for {window_id}: {hwnd}")
                    return False  # Stop enumeration
            return True

        win32gui.EnumWindows(callback, None)

        if not hwnd:
            # Try alternative approach
            hwnd = win32gui.FindWindow(None, window_id)

        return hwnd

    def set_window_mode(self, window_id, mode):
        """Set mode for a specific window dynamically"""
        max_attempts = 10
        hwnd = None

        # Try to find the window with retries
        for attempt in range(max_attempts):
            hwnd = self.find_window_handle(window_id)
            if hwnd:
                break
            time.sleep(0.2)

        if not hwnd:
            print(f"[WARN] Window {window_id} not found after {max_attempts} attempts.")
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

        print(f"[INFO] Window '{window_id}' mode changed to {mode}.")
        return True

    def toggle_mode(self, window_id):
        """Convenience method to switch between normal and click-through"""
        current = self.window_modes.get(window_id, 1)
        new_mode = 2 if current == 1 else 1
        self.set_window_mode(window_id, new_mode)
        return new_mode

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
            import json
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
        except Exception as e:
            print(f"[WARN] Failed to push data to {window_id}: {e}")

    def stop(self):
        """Stop telemetry updates and close windows"""
        print("[INFO] Stopping WindowManager...")
        self._running = False
        for window_id, window in self.windows.items():
            try:
                window.destroy()
                print(f"[INFO] Closed window {window_id}")
            except Exception:
                pass
        print("[INFO] All windows closed.")

    def race_table_update(self, data):
        """Handle race table update"""
        self.logger.info(f"[WindowManager] Received race-table-update ({len(data)} bytes)")
        self.unicast_data("lap_timer", data)
