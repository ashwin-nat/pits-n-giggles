import webview
import threading
import time
import random
import ctypes
import win32gui
import win32con
import signal
import sys

from typing import Dict

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
    def __init__(self):
        self.windows: Dict[str, webview.Window] = {}
        self.apis: Dict[str, API] = {}
        self.window_modes: Dict[str, int] = {}
        self._running = True

    def create_window(self, window_id, x=100, y=100, initial_mode=2):
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
            'index.html',
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

    def update_window_data(self, window_id, data):
        if window_id in self.apis:
            self.apis[window_id].data.update(data)

    def broadcast_data(self, data):
        for api in self.apis.values():
            api.data.update(data)

    def unicast_data(self, window_id, data):
        window = self.apis.get(window_id)
        if window:
            window.data.update(data)

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

def update_telemetry(manager: WindowManager):
    """Background thread that updates telemetry data"""
    lap_time = 0.0
    while manager._running:
        time.sleep(0.1)
        data = {
            'speed': random.randint(0, 320),
            'rpm': random.randint(1000, 8000),
            'gear': random.randint(1, 6)
        }
        lap_time += 0.1
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        data['lap_time'] = f"{minutes}:{seconds:06.3f}"
        manager.broadcast_data(data)

manager = WindowManager()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[INFO] Received interrupt signal. Shutting down...")
    manager.stop()
    sys.exit(0)

def main():
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Each window can now have its own mode
    manager.create_window('window1', x=100, y=100, initial_mode=2)
    manager.create_window('window2', x=550, y=100, initial_mode=2)

    telemetry_thread = threading.Thread(target=update_telemetry, args=(manager,), daemon=True)
    telemetry_thread.start()

    try:
        webview.start(debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()

if __name__ == '__main__':
    main()
