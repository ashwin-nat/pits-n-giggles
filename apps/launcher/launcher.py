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

import os
import sys
import tkinter as tk
from pathlib import Path

from apps.launcher.png_launcher import PngLauncher

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        # Running from PyInstaller bundle
        return Path(sys._MEIPASS) / relative_path
    else:
        # Running from source
        return Path(__file__).parent.parent.parent / relative_path

def get_version() -> str:
    """Get the version string from env variable

    Returns:
        str: Version string
    """

    return os.environ.get('PNG_VERSION', 'dev')

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

APP_ICON_PATH = str(resource_path("assets/logo.png"))
SETTINGS_ICON_PATH = str(resource_path("assets/settings.ico"))

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    root = tk.Tk()
    root.title("Pits n' Giggles")
    root.iconbitmap(resource_path("assets/favicon.ico"))  # Set the icon for the main window
    app = PngLauncher(
        root=root,
        ver_str=get_version(),
        logo_path=APP_ICON_PATH,
        settings_icon_path=SETTINGS_ICON_PATH,
        debug_mode=debug_mode
    )
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
