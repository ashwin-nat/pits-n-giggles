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
import shutil
import sys
import tempfile
import tkinter as tk

from apps.launcher.png_launcher import PngLauncher
from lib.version import get_version

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_icon_safely(icon_relative_path):
    """
    Workaround for tkinter.iconbitmap() failing to load .ico from _MEIPASS.
    """
    icon_path = resource_path(icon_relative_path)

    if getattr(sys, 'frozen', False):
        # Copy .ico file to a real temp file so tkinter can access it
        tmp_fd, tmp_icon_path = tempfile.mkstemp(suffix=".ico")
        os.close(tmp_fd)
        shutil.copyfile(icon_path, tmp_icon_path)
        return tmp_icon_path
    else:
        return icon_path

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

APP_ICON_PATH = str(resource_path("assets/logo.png"))
SETTINGS_ICON_PATH = str(resource_path("assets/settings.ico"))

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    debug_mode = "--debug" in sys.argv
    root = tk.Tk()
    root.title("Pits n' Giggles")
    root.iconbitmap(load_icon_safely("assets/favicon.ico"))  # Set the icon for the main window
    app = PngLauncher(
        root=root,
        ver_str=get_version(),
        logo_path=APP_ICON_PATH,
        settings_icon_path=SETTINGS_ICON_PATH,
        debug_mode=debug_mode
    )
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
