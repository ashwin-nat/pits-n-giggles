# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

import sys
import tkinter as tk
from pathlib import Path

from .launcher import PngLancher

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

ICON_PATH = str(Path.cwd() / "assets" / "logo.png")

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    root = tk.Tk()
    root.title("Pits n' Giggles")
    root.iconbitmap("assets/favicon.ico")  # Set the icon for the main window
    app = PngLancher(root, ICON_PATH, debug_mode=debug_mode)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
