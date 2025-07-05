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

import importlib.util
import os
import runpy
import shutil
import sys
import tempfile
import tkinter as tk
from pathlib import Path

from apps.launcher.png_launcher import PngLauncher
from lib.version import get_version

print("\nlauncher starting...\n")
# Prevent fork bomb: if launcher is launched via `-m`, kill immediately and log

if getattr(sys, 'frozen', False):
    log_path = Path(sys.executable).with_name("launcher_entry.log")
    with log_path.open("a", encoding="utf-8") as f:
        f.write("[LAUNCHER ENTERED]\n")
        f.write(f"sys.argv: {sys.argv}\n")

print('fork bomb check passed\n')

# Force PyInstaller to include __main__.py files
if False:
    import apps.backend.__main__
    import apps.save_viewer.__main__

if getattr(sys, 'frozen', False) and '--module' in sys.argv:
    idx = sys.argv.index('--module')
    module = sys.argv[idx + 1]
    args = sys.argv[idx + 2:]

    sys.path.insert(0, os.path.join(sys._MEIPASS))

    print(f"[dispatcher] sys.path = {sys.path}")
    print(f"[dispatcher] attempting run_module('{module}')")

    # Check whether the module can be found
    spec = importlib.util.find_spec(module)
    if spec is None:
        print(f"[dispatcher] Module '{module}' NOT FOUND in sys.path")
    else:
        print(f"[dispatcher] Module '{module}' found at: {spec.origin}")

    sys.argv = [module] + args

    try:
        runpy.run_module(module, run_name="__main__")
    except Exception as e:
        print(f"[dispatcher] Exception during run_module: {e}")
        import traceback
        traceback.print_exc()

    sys.exit(0)

print(">> running launcher main()")

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
    print(">> running launcher entry_point()")
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
