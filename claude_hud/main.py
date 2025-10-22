import webview
import threading
import time
import random
import ctypes
import win32gui
import win32con

from typing import Dict

# Global config - set to 1 or 2
INITIAL_MODE = 2  # 1 = normal, 2 = click-through frameless

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

    def log(self, message):
        print(f"[{self.window_id} JS]: {message}")

class WindowManager:
    def __init__(self):
        self.windows = {}
        self.apis: Dict[str, API] = {}

    def create_window(self, window_id, x=100, y=100):
        """Create a new overlay window"""
        api = API(window_id)
        self.apis[window_id] = api

        frameless = (INITIAL_MODE == 2)
        resizable = (INITIAL_MODE == 1)

        window = webview.create_window(
            f'Sim Racing Overlay {window_id}',
            'index.html',
            js_api=api,
            width=400,
            height=300,
            x=x,
            y=y,
            frameless=frameless,
            on_top=True,
            resizable=resizable,
        )

        self.windows[window_id] = window

        # 🔥 Patch console.log in the browser to redirect to Python
        def inject_logger():
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
            window.evaluate_js(js_code)

        # Delay injection slightly so the DOM is ready
        threading.Timer(1.0, inject_logger).start()

        # Apply mode after the window is fully created
        threading.Timer(0.5, lambda: self.set_window_mode(window_id, INITIAL_MODE)).start()

        return window

    def set_window_mode(self, window_id, mode):
        """Set mode for a specific window"""
        hwnd = win32gui.FindWindow(None, f'Sim Racing Overlay {window_id}')
        if not hwnd:
            return False

        if mode == 1:
            # Normal window with controls and resize
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style &= ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style |= win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_THICKFRAME
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        else:
            # Frameless, click-through
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style |= (
                win32con.WS_EX_LAYERED |
                win32con.WS_EX_TRANSPARENT|
                win32con.WS_EX_NOACTIVATE |
                win32con.WS_EX_TOOLWINDOW
            )
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

            # Fully visible (255 alpha)
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

        return True

    def update_window_data(self, window_id, data):
        """Update data for a specific window"""
        if window_id in self.apis:
            self.apis[window_id].data.update(data)

    def broadcast_data(self, data):
        """Update data for all windows"""
        for api in self.apis.values():
            api.data.update(data)

    def unicast_data(self, window_id, data):
        """Update data for a specific window only"""
        window = self.apis.get(window_id)
        if not window_id:
            return
        window.data.update(data)

def update_telemetry(manager: WindowManager):
    """Background thread that updates telemetry data"""
    lap_time = 0.0
    while True:
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

def main():
    manager.create_window('window1', x=100, y=100)
    manager.create_window('window2', x=550, y=100)

    telemetry_thread = threading.Thread(target=update_telemetry, args=(manager,), daemon=True)
    telemetry_thread.start()

    webview.start()

if __name__ == '__main__':
    main()
