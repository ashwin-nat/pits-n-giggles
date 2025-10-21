import webview
import ctypes

# --- CONFIG ---
LOCKED = False  # Toggle this to lock/unlock overlay

# --- HTML CONTENT ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<style>
body {
  margin: 0;
  background: transparent;
  color: lime;
  font-family: Consolas, monospace;
  font-size: 24px;
  text-align: center;
  padding-top: 40px;
}
</style>
</head>
<body>
Speed: 217 km/h<br>
Gear: 6
</body>
</html>
"""

# --- Windows API setup ---
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x20
WS_EX_LAYERED = 0x80000

def set_clickthrough(hwnd):
    """Make the window ignore mouse clicks."""
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

def clear_clickthrough(hwnd):
    """Restore click handling."""
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT)

# --- Window creation ---
window = webview.create_window(
    title="Overlay",
    html=HTML_PAGE,
    width=400,
    height=200,
    frameless=LOCKED,      # No title bar when locked
    transparent=True,
    on_top=True,
    resizable=not LOCKED,  # Allow resizing only when unlocked
)

def on_loaded():
    hwnd = window.gui.window
    if LOCKED:
        set_clickthrough(hwnd)
    else:
        clear_clickthrough(hwnd)

webview.start(on_loaded)
