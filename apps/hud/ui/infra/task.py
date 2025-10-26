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

import logging
import os

from .infra import WindowManager

# -------------------------------------- FUNCTIONS -----------------------------------------------------------------------

def _get_html_path_for_window(window_id: str) -> str:
    """Constructs the absolute path to the HTML file for a given window ID."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(base_dir, "..", "overlays", window_id, f"{window_id}.html")
    return html_file_path

def get_window_manager(logger: logging.Logger) -> WindowManager:
    """Returns the global WindowManager instance."""

    manager = WindowManager(logger)
    manager.create_window(
        window_id="lapTimer",
        html_path=_get_html_path_for_window("lapTimer"))

    return manager
