import webview
import threading
import time
import random

# Global config - set to 1 or 2
INITIAL_MODE = 1  # 1 = normal with controls, 2 = click-through frameless

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

class WindowManager:
    def __init__(self):
        self.windows = {}
        self.apis = {}

    def create_window(self, window_id, x=100, y=100):
        """Create a new overlay window"""
        api = API(window_id)
        self.apis[window_id] = api

        # Set window properties based on initial mode
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
            resizable=resizable
        )

        self.windows[window_id] = window

        return window

    def set_window_mode(self, window_id, mode):
        """Set mode for a specific window - call this after windows are fully loaded"""
        import win32gui
        import win32con

        hwnd = win32gui.FindWindow(None, f'Sim Racing Overlay {window_id}')
        if not hwnd:
            return False

        if mode == 1:
            # Mode 1: Normal window with controls and resize
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style = style & ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)

            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style = style | win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_THICKFRAME
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        else:
            # Mode 2: Frameless, click-through, no resize
            win32gui.SetWindowLong(
                hwnd,
                win32con.GWL_EXSTYLE,
                win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            )

            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style = style & ~win32con.WS_CAPTION & ~win32con.WS_SYSMENU & ~win32con.WS_THICKFRAME
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

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

def update_telemetry(manager):
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
    global manager

    # Create windows
    manager.create_window('window1', x=100, y=100)
    manager.create_window('window2', x=550, y=100)

    # Start telemetry thread
    telemetry_thread = threading.Thread(target=update_telemetry, args=(manager,), daemon=True)
    telemetry_thread.start()

    # Start webview - IMPORTANT: debug=False to avoid recursion errors
    webview.start(debug=False)

if __name__ == '__main__':
    main()